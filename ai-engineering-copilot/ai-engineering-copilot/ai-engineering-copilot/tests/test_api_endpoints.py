"""
Integration tests for the API layer. These exercise the FastAPI app
directly (no live server), using SQLite in place of Postgres and the
mock LLM provider in place of a real one (see conftest.py). GitHub
cloning is monkeypatched since tests must not depend on network access.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database.database as database_module
import main
from database.database import Base, get_db
from services import github


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Isolated SQLite DB per test. StaticPool ensures every session shares
    # the same in-memory connection (plain in-memory SQLite is otherwise
    # per-connection, which would give each request a fresh, empty DB).
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = override_get_db

    # Fake a successful clone into a temp dir with one Python file,
    # so tests never touch the network.
    repo_dir = tmp_path / "acme__widgets"
    repo_dir.mkdir()
    (repo_dir / "auth.py").write_text(
        "def authenticate_user(token):\n"
        "    \"\"\"Validate a bearer token against the configured secret.\"\"\"\n"
        "    return token == 'secret'\n"
    )

    def fake_clone_repository(owner, repo):
        return github.CloneResult(local_path=repo_dir, default_branch="main")

    monkeypatch.setattr(github, "clone_repository", fake_clone_repository)
    monkeypatch.setattr("api.repositories.github.clone_repository", fake_clone_repository)

    with TestClient(main.app) as test_client:
        yield test_client

    main.app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_repository_rejects_invalid_url(client):
    response = client.post("/api/repositories", json={"github_url": "not-a-url"})
    assert response.status_code == 422


def test_create_and_list_repository(client):
    response = client.post(
        "/api/repositories", json={"github_url": "https://github.com/acme/widgets"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["owner"] == "acme"
    assert body["name"] == "widgets"
    assert body["file_count"] == 1

    list_response = client.get("/api/repositories")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_full_import_index_chat_flow(client):
    create_response = client.post(
        "/api/repositories", json={"github_url": "https://github.com/acme/widgets"}
    )
    repo_id = create_response.json()["id"]

    index_response = client.post(f"/api/repositories/{repo_id}/index")
    assert index_response.status_code == 200
    indexed_repo = index_response.json()
    assert indexed_repo["index_status"] == "ready"
    assert indexed_repo["chunk_count"] >= 1

    chat_response = client.post(
        f"/api/repositories/{repo_id}/chat", json={"question": "How does authentication work?"}
    )
    assert chat_response.status_code == 200
    chat_body = chat_response.json()
    assert "answer" in chat_body
    assert "sources" in chat_body


def test_chat_before_indexing_returns_conflict(client):
    create_response = client.post(
        "/api/repositories", json={"github_url": "https://github.com/acme/widgets"}
    )
    repo_id = create_response.json()["id"]

    chat_response = client.post(
        f"/api/repositories/{repo_id}/chat", json={"question": "How does auth work?"}
    )
    assert chat_response.status_code == 409


def test_review_endpoint_accepts_pasted_diff(client):
    response = client.post(
        "/api/review",
        json={"diff": "+ def foo():\n+     return eval(user_input)"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "summary" in body
    assert "issues" in body


def test_review_endpoint_requires_some_input(client):
    response = client.post("/api/review", json={})
    assert response.status_code == 422


def test_file_content_endpoint_blocks_path_traversal(client):
    create_response = client.post(
        "/api/repositories", json={"github_url": "https://github.com/acme/widgets"}
    )
    repo_id = create_response.json()["id"]

    response = client.get(f"/api/repositories/{repo_id}/files/../../etc/passwd")
    assert response.status_code in (400, 404)
