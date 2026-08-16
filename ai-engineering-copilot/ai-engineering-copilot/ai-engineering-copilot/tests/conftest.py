"""
Shared pytest fixtures. Tests use SQLite in-memory instead of Postgres
so they run without any external services, and the "mock" LLM provider
instead of real API calls.
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from database.database import Base  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
