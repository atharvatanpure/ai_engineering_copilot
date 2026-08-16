from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agents.chat_agent import answer_question
from database import models, schemas
from database.database import get_db

router = APIRouter(prefix="/api/repositories", tags=["chat"])


@router.post("/{repository_id}/chat", response_model=schemas.ChatResponse)
def chat_with_repository(
    repository_id: str, payload: schemas.ChatRequest, db: Session = Depends(get_db)
):
    repo = db.get(models.Repository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    if repo.index_status != models.IndexStatus.READY:
        raise HTTPException(
            status_code=409,
            detail=f"Repository is not ready for chat (status: {repo.index_status.value}). "
            "Index it first via POST /api/repositories/{id}/index.",
        )

    session = None
    if payload.session_id:
        session = db.get(models.ChatSession, payload.session_id)
    if not session:
        session = models.ChatSession(repository_id=repository_id, title=payload.question[:80])
        db.add(session)
        db.flush()

    db.add(models.ChatMessage(session_id=session.id, role="user", content=payload.question))

    result = answer_question(repo, payload.question)

    db.add(
        models.ChatMessage(
            session_id=session.id,
            role="assistant",
            content=result.answer,
            sources=result.sources,
        )
    )
    db.commit()

    return schemas.ChatResponse(
        session_id=session.id,
        answer=result.answer,
        sources=[schemas.SourceCitation(**s) for s in result.sources],
        grounded=result.grounded,
    )
