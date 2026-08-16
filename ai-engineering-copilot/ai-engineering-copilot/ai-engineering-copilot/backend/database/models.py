import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class IndexStatus(str, enum.Enum):
    PENDING = "pending"
    CLONING = "cloning"
    SCANNING = "scanning"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class Repository(Base):
    __tablename__ = "repositories"
    __table_args__ = (UniqueConstraint("owner", "name", name="uq_owner_name"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    github_url: Mapped[str] = mapped_column(String, nullable=False)
    owner: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    default_branch: Mapped[str] = mapped_column(String, default="main")
    languages: Mapped[dict] = mapped_column(JSON, default=dict)  # {"python": 42, "typescript": 10}
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    line_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    index_status: Mapped[IndexStatus] = mapped_column(
        Enum(IndexStatus), default=IndexStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_path: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    last_analyzed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    files: Mapped[list["RepositoryFile"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )


class RepositoryFile(Base):
    __tablename__ = "repository_files"
    __table_args__ = (UniqueConstraint("repository_id", "file_path", name="uq_repo_file"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"))
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    line_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    indexed: Mapped[bool] = mapped_column(default=False)

    repository: Mapped["Repository"] = relationship(back_populates="files")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"))
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    repository: Mapped["Repository"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id"))
    role: Mapped[str] = mapped_column(String, nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list] = mapped_column(JSON, default=list)  # [{file_path, start_line, end_line}]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class ReviewResult(Base):
    __tablename__ = "review_results"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    repository_id: Mapped[str | None] = mapped_column(
        ForeignKey("repositories.id"), nullable=True
    )
    target_description: Mapped[str] = mapped_column(String, default="")  # e.g. file path or "pasted diff"
    summary: Mapped[str] = mapped_column(Text, default="")
    issues: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
