from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------- Repository ----------

class RepositoryCreate(BaseModel):
    github_url: str = Field(..., examples=["https://github.com/tiangolo/fastapi"])


class RepositoryOut(BaseModel):
    id: str
    github_url: str
    owner: str
    name: str
    default_branch: str
    languages: dict[str, int]
    file_count: int
    line_count: int
    chunk_count: int
    index_status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    last_analyzed_at: datetime | None = None

    class Config:
        from_attributes = True


class RepositoryFileOut(BaseModel):
    file_path: str
    language: str | None
    line_count: int
    size_bytes: int
    indexed: bool

    class Config:
        from_attributes = True


# ---------- Chat ----------

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class SourceCitation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    symbol: str | None = None
    snippet: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceCitation]
    grounded: bool  # False if the model said it couldn't find enough context


# ---------- Code Review ----------

class ReviewRequest(BaseModel):
    repository_id: str | None = None
    file_path: str | None = None
    diff: str | None = None
    code: str | None = None


class ReviewIssue(BaseModel):
    severity: Literal["critical", "high", "medium", "low", "info"]
    category: Literal["bug", "security", "performance", "maintainability", "best_practice"]
    file: str | None = None
    line: int | None = None
    title: str
    description: str
    recommendation: str


class ReviewResponse(BaseModel):
    id: str
    summary: str
    issues: list[ReviewIssue]
