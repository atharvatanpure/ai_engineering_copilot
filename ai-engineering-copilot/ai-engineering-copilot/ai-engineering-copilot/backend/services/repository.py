"""
Orchestrates repository import: scanning the cloned filesystem tree,
computing statistics, and persisting Repository / RepositoryFile rows.
Untrusted repository content is only ever *read as text*, never
executed, imported, or evaluated.
"""
from dataclasses import dataclass, field
from pathlib import Path

from config import get_settings
from utils.ignore_patterns import (
    detect_language,
    is_binary_or_media,
    is_ignored_dir,
    looks_generated_or_minified,
)

settings = get_settings()


class EmptyRepositoryError(Exception):
    pass


@dataclass
class ScannedFile:
    relative_path: str
    absolute_path: Path
    language: str | None
    line_count: int
    size_bytes: int
    text: str


@dataclass
class ScanResult:
    files: list[ScannedFile] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)  # language -> file count
    total_files: int = 0
    total_lines: int = 0
    truncated: bool = False  # True if max_indexed_files limit was hit


def scan_repository(local_path: Path) -> ScanResult:
    result = ScanResult()
    max_file_bytes = settings.max_file_size_kb * 1024

    for path in sorted(local_path.rglob("*")):
        if path.is_dir():
            continue
        if any(is_ignored_dir(part) for part in path.relative_to(local_path).parts[:-1]):
            continue
        if is_ignored_dir(path.parent.name):
            continue
        if is_binary_or_media(path):
            continue

        try:
            size_bytes = path.stat().st_size
        except OSError:
            continue
        if size_bytes == 0 or size_bytes > max_file_bytes:
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue  # skip non-text / undecodable files

        if looks_generated_or_minified(text):
            continue

        language = detect_language(path)
        line_count = text.count("\n") + 1

        relative_path = str(path.relative_to(local_path))
        result.files.append(
            ScannedFile(
                relative_path=relative_path,
                absolute_path=path,
                language=language,
                line_count=line_count,
                size_bytes=size_bytes,
                text=text,
            )
        )
        result.total_files += 1
        result.total_lines += line_count
        if language:
            result.languages[language] = result.languages.get(language, 0) + 1

        if result.total_files >= settings.max_indexed_files:
            result.truncated = True
            break

    if result.total_files == 0:
        raise EmptyRepositoryError(
            "No indexable source files were found in this repository "
            "(after excluding binaries, generated files, and ignored directories)."
        )

    return result
