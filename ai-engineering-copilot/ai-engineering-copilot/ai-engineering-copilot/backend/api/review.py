from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agents.review_agent import review_code
from database import models, schemas
from database.database import get_db
from utils.security import PathTraversalError, safe_join

router = APIRouter(prefix="/api", tags=["review"])


@router.post("/review", response_model=schemas.ReviewResponse)
def run_review(payload: schemas.ReviewRequest, db: Session = Depends(get_db)):
    if not payload.diff and not payload.code and not payload.file_path:
        raise HTTPException(
            status_code=422, detail="Provide a 'diff', raw 'code', or a 'file_path' within a repository."
        )

    code = payload.code
    file_label = payload.file_path

    if payload.file_path and not payload.code and not payload.diff:
        if not payload.repository_id:
            raise HTTPException(
                status_code=422, detail="'repository_id' is required when reviewing by file_path."
            )
        repo = db.get(models.Repository, payload.repository_id)
        if not repo or not repo.local_path:
            raise HTTPException(status_code=404, detail="Repository not found or not cloned.")
        try:
            resolved = safe_join(Path(repo.local_path), payload.file_path)
        except PathTraversalError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not resolved.exists() or not resolved.is_file():
            raise HTTPException(status_code=404, detail="File not found in repository.")
        try:
            code = resolved.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=415, detail="File is not a supported text format.") from exc

    result = review_code(file_path=file_label, code=code, diff=payload.diff)

    record = models.ReviewResult(
        repository_id=payload.repository_id,
        target_description=payload.file_path or ("pasted diff" if payload.diff else "pasted code"),
        summary=result.get("summary", ""),
        issues=result.get("issues", []),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return schemas.ReviewResponse(id=record.id, summary=record.summary, issues=record.issues)
