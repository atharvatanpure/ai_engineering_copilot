from rag.chunker import chunk_file

PY_SOURCE = '''\
import os

CONSTANT = 42


def authenticate_user(token: str) -> bool:
    """Validate a bearer token."""
    if not token:
        return False
    return token == "secret"


class AuthService:
    def __init__(self, secret: str):
        self.secret = secret

    def login(self, username: str, password: str) -> str:
        return "token"
'''

TS_SOURCE = """\
export function greet(name: string): string {
  return `hello ${name}`;
}

export class Greeter {
  greet() {
    return "hi";
  }
}
"""


def test_python_chunking_splits_on_functions_and_classes():
    chunks = chunk_file("service.py", "python", PY_SOURCE)
    symbols = {c.symbol for c in chunks}

    assert "authenticate_user" in symbols
    assert "AuthService" in symbols
    # every chunk has valid metadata
    for c in chunks:
        assert c.file_path == "service.py"
        assert c.language == "python"
        assert c.start_line >= 1
        assert c.end_line >= c.start_line
        assert c.text.strip() != ""


def test_python_chunking_handles_syntax_errors_gracefully():
    broken_source = "def foo(:\n    pass\n"
    chunks = chunk_file("broken.py", "python", broken_source)
    assert len(chunks) >= 1  # falls back to generic chunking, doesn't crash


def test_generic_chunking_finds_declarations():
    chunks = chunk_file("greet.ts", "typescript", TS_SOURCE)
    symbols = [c.symbol for c in chunks if c.symbol]
    assert any("greet" in (s or "") for s in symbols) or any(
        "Greeter" in (s or "") for s in symbols
    )


def test_chunk_file_returns_empty_list_for_blank_source():
    assert chunk_file("empty.py", "python", "   \n\n") == []
