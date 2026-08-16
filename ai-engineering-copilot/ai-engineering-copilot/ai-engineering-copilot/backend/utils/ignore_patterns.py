"""
Rules for deciding which files/directories are relevant to index.
"""
from pathlib import Path

IGNORED_DIR_NAMES = {
    ".git", "node_modules", "__pycache__", ".next", "dist", "build",
    "venv", ".venv", "env", ".env", "target", ".idea", ".vscode",
    "coverage", ".pytest_cache", ".mypy_cache", "vendor", ".tox",
    "site-packages", ".terraform", "out",
}

BINARY_OR_MEDIA_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
    ".mp4", ".mov", ".avi", ".mkv", ".webm",
    ".mp3", ".wav", ".flac", ".ogg",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".class", ".o", ".a",
    ".db", ".sqlite", ".sqlite3", ".lock",
    ".pyc", ".pyo",
}

LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".kt": "kotlin",
    ".swift": "swift",
    ".scala": "scala",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sql": "sql",
    ".sh": "shell",
}

MAX_GENERATED_FILE_LINE_LENGTH = 2000  # heuristic for minified/generated files


def is_ignored_dir(dir_name: str) -> bool:
    return dir_name in IGNORED_DIR_NAMES or dir_name.startswith(".")


def is_binary_or_media(path: Path) -> bool:
    return path.suffix.lower() in BINARY_OR_MEDIA_EXTENSIONS


def detect_language(path: Path) -> str | None:
    return LANGUAGE_BY_EXTENSION.get(path.suffix.lower())


def looks_generated_or_minified(text: str) -> bool:
    """Heuristic: very long lines usually indicate minified/generated code."""
    for line in text.splitlines()[:20]:
        if len(line) > MAX_GENERATED_FILE_LINE_LENGTH:
            return True
    return False
