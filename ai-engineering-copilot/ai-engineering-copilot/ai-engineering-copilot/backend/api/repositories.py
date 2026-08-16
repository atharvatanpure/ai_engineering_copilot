from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import models, schemas
from database.database import get_db
from rag.indexer import index_repository
from services import github, repository as repo_service
from services.llm.base import LLMError
from utils.security import InvalidGitHubURLError, PathTraversalError, parse_github_url, safe_join

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.post("", response_model=schemas.RepositoryOut, status_code=201)
def create_repository(payload: schemas.RepositoryCreate, db: Session = Depends(get_db)):
    try:
        owner, name = parse_github_url(payload.github_url)
    except InvalidGitHubURLError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    existing = (
        db.query(models.Repository)
        .filter(models.Repository.owner == owner, models.Repository.name == name)
        .first()
    )
    if existing:
        return existing

    repo = models.Repository(
        github_url=payload.github_url,
        owner=owner,
        name=name,
        index_status=models.IndexStatus.CLONING,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    try:
        clone_result = github.clone_repository(owner, name)
    except github.RepositoryNotFoundError as exc:
        _fail(db, repo, str(exc))
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except github.PrivateRepositoryError as exc:
        _fail(db, repo, str(exc))
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except github.RepositoryTooLargeError as exc:
        _fail(db, repo, str(exc))
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except github.CloneFailedError as exc:
        _fail(db, repo, str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    repo.local_path = str(clone_result.local_path)
    repo.default_branch = clone_result.default_branch
    repo.index_status = models.IndexStatus.SCANNING
    db.commit()

    try:
        scan = repo_service.scan_repository(clone_result.local_path)
    except repo_service.EmptyRepositoryError as exc:
        _fail(db, repo, str(exc))
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    repo.file_count = scan.total_files
    repo.line_count = scan.total_lines
    repo.languages = scan.languages
    repo.index_status = models.IndexStatus.PENDING
    db.commit()
    db.refresh(repo)
    return repo


@router.get("", response_model=list[schemas.RepositoryOut])
def list_repositories(db: Session = Depends(get_db)):
    return db.query(models.Repository).order_by(models.Repository.created_at.desc()).all()


@router.get("/{repository_id}", response_model=schemas.RepositoryOut)
def get_repository(repository_id: str, db: Session = Depends(get_db)):
    repo = db.get(models.Repository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repo


@router.post("/{repository_id}/index", response_model=schemas.RepositoryOut)
def reindex_repository(repository_id: str, db: Session = Depends(get_db)):
    from datetime import datetime, timezone

    repo = db.get(models.Repository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    if not repo.local_path:
        raise HTTPException(status_code=409, detail="Repository has not been cloned successfully yet.")

    repo.index_status = models.IndexStatus.INDEXING
    db.commit()

    try:
        from pathlib import Path

        scan = repo_service.scan_repository(Path(repo.local_path))
        chunk_count = index_repository(db, repo, scan)
    except repo_service.EmptyRepositoryError as exc:
        _fail(db, repo, str(exc))
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMError as exc:
        _fail(db, repo, f"Embedding failed: {exc}")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # vector DB / unexpected failures
        _fail(db, repo, f"Indexing failed: {exc}")
        raise HTTPException(status_code=500, detail="Indexing failed. See error_message for details.") from exc

    repo.chunk_count = chunk_count
    repo.file_count = scan.total_files
    repo.line_count = scan.total_lines
    repo.languages = scan.languages
    repo.index_status = models.IndexStatus.READY
    repo.error_message = None
    repo.last_analyzed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(repo)
    return repo


@router.get("/{repository_id}/files", response_model=list[schemas.RepositoryFileOut])
def list_files(repository_id: str, db: Session = Depends(get_db)):
    repo = db.get(models.Repository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return (
        db.query(models.RepositoryFile)
        .filter(models.RepositoryFile.repository_id == repository_id)
        .order_by(models.RepositoryFile.file_path)
        .all()
    )


@router.get("/{repository_id}/files/{file_path:path}")
def get_file_content(repository_id: str, file_path: str, db: Session = Depends(get_db)):
    repo = db.get(models.Repository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    if not repo.local_path:
        raise HTTPException(status_code=409, detail="Repository has not been cloned.")

    from pathlib import Path

    try:
        resolved = safe_join(Path(repo.local_path), file_path)
    except PathTraversalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found in repository.")

    try:
        content = resolved.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=415, detail="File is not a supported text format.") from exc

    return {"file_path": file_path, "content": content}


def _fail(db: Session, repo: models.Repository, message: str) -> None:
    repo.index_status = models.IndexStatus.FAILED
    repo.error_message = message[:1000]
    db.commit()
