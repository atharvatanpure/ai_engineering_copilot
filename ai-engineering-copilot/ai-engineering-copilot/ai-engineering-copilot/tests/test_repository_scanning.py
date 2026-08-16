from pathlib import Path

import pytest

from services.repository import EmptyRepositoryError, scan_repository


def _write(path: Path, content: str = "print('hi')\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_scan_ignores_irrelevant_dirs_and_binaries(tmp_path: Path):
    _write(tmp_path / "src" / "main.py")
    _write(tmp_path / "node_modules" / "pkg" / "index.js")
    _write(tmp_path / ".git" / "config")
    _write(tmp_path / "__pycache__" / "main.cpython-311.pyc")
    (tmp_path / "logo.png").write_bytes(b"\x89PNG\r\n")

    result = scan_repository(tmp_path)

    relative_paths = {f.relative_path for f in result.files}
    assert "src/main.py" in relative_paths
    assert not any("node_modules" in p for p in relative_paths)
    assert not any(".git" in p for p in relative_paths)
    assert not any("__pycache__" in p for p in relative_paths)
    assert "logo.png" not in relative_paths


def test_scan_detects_language_and_counts(tmp_path: Path):
    _write(tmp_path / "app.py", "def foo():\n    return 1\n")
    _write(tmp_path / "index.ts", "export const x = 1;\n")

    result = scan_repository(tmp_path)

    assert result.languages.get("python") == 1
    assert result.languages.get("typescript") == 1
    assert result.total_files == 2
    assert result.total_lines >= 2


def test_scan_raises_on_empty_repository(tmp_path: Path):
    (tmp_path / "node_modules").mkdir()
    _write(tmp_path / "node_modules" / "index.js")

    with pytest.raises(EmptyRepositoryError):
        scan_repository(tmp_path)
