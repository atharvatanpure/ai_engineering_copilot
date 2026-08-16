"""
Splits source files into semantically meaningful chunks rather than
naive fixed-size windows.

- Python: uses the standard library `ast` module to chunk on function
  and class boundaries, falling back to line windows for very large
  functions or module-level code between definitions.
- Other languages: uses a regex-based heuristic that recognizes common
  function/class/method declaration patterns (JS/TS, Go, Java, Rust,
  etc.) to find natural split points, falling back to fixed-size line
  windows with overlap when no structure is detected.

Every chunk carries metadata: repository, file_path, language,
start_line, end_line, symbol.
"""
import ast
import re
from dataclasses import dataclass

from config import get_settings

settings = get_settings()

# Heuristic declaration patterns per language family, used only to find
# good split boundaries — not a real parser.
_DECL_PATTERNS = [
    re.compile(r"^\s*(export\s+)?(default\s+)?(async\s+)?function\s+([A-Za-z0-9_$]+)"),
    re.compile(r"^\s*(export\s+)?(default\s+)?class\s+([A-Za-z0-9_$]+)"),
    re.compile(r"^\s*(export\s+)?const\s+([A-Za-z0-9_$]+)\s*=\s*(async\s*)?\("),  # arrow fns
    re.compile(r"^\s*func\s+(\([^)]*\)\s*)?([A-Za-z0-9_]+)\s*\("),  # go
    re.compile(r"^\s*(public|private|protected|static|\s)*[\w<>\[\]]+\s+([A-Za-z0-9_]+)\s*\("),  # java/c#
    re.compile(r"^\s*(pub\s+)?fn\s+([A-Za-z0-9_]+)"),  # rust
    re.compile(r"^\s*def\s+([A-Za-z0-9_]+)"),  # ruby / fallback
]


@dataclass
class CodeChunk:
    file_path: str
    language: str
    start_line: int
    end_line: int
    symbol: str | None
    text: str


def chunk_python_file(file_path: str, source: str) -> list[CodeChunk]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return chunk_generic_file(file_path, "python", source)

    lines = source.splitlines()
    chunks: list[CodeChunk] = []
    covered_lines: set[int] = set()

    top_level_defs = [
        node for node in ast.iter_child_nodes(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]

    for node in top_level_defs:
        start = node.lineno
        end = getattr(node, "end_lineno", node.lineno)
        symbol = node.name
        chunk_text = "\n".join(lines[start - 1:end])
        chunks.extend(
            _split_if_too_long(file_path, "python", symbol, start, end, chunk_text)
        )
        covered_lines.update(range(start, end + 1))

    # Capture module-level code (imports, constants, top-level statements)
    # not covered by any function/class, as its own chunk(s).
    remaining = [i + 1 for i in range(len(lines)) if (i + 1) not in covered_lines and lines[i].strip()]
    if remaining:
        for group_start, group_end in _group_consecutive(remaining):
            text = "\n".join(lines[group_start - 1:group_end])
            if text.strip():
                chunks.append(
                    CodeChunk(file_path, "python", group_start, group_end, "<module-level>", text)
                )

    chunks.sort(key=lambda c: c.start_line)
    return chunks or chunk_generic_file(file_path, "python", source)


def chunk_generic_file(file_path: str, language: str, source: str) -> list[CodeChunk]:
    lines = source.splitlines()
    if not lines:
        return []

    boundaries: list[tuple[int, str]] = []  # (line_index_0based, symbol)
    for idx, line in enumerate(lines):
        for pattern in _DECL_PATTERNS:
            match = pattern.match(line)
            if match:
                symbol = match.group(match.lastindex) if match.lastindex else None
                boundaries.append((idx, symbol or "<block>"))
                break

    max_lines = settings.max_chunk_lines
    overlap = settings.chunk_overlap_lines

    if not boundaries:
        return _fixed_window_chunks(file_path, language, lines, max_lines, overlap)

    chunks: list[CodeChunk] = []
    for i, (start_idx, symbol) in enumerate(boundaries):
        end_idx = boundaries[i + 1][0] - 1 if i + 1 < len(boundaries) else len(lines) - 1
        start_line, end_line = start_idx + 1, end_idx + 1
        text = "\n".join(lines[start_idx:end_idx + 1])
        chunks.extend(
            _split_if_too_long(file_path, language, symbol, start_line, end_line, text)
        )

    if boundaries[0][0] > 0:
        head_text = "\n".join(lines[0:boundaries[0][0]])
        if head_text.strip():
            chunks.insert(
                0, CodeChunk(file_path, language, 1, boundaries[0][0], "<module-level>", head_text)
            )

    return chunks


def _split_if_too_long(
    file_path: str, language: str, symbol: str, start_line: int, end_line: int, text: str
) -> list[CodeChunk]:
    max_lines = settings.max_chunk_lines
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return [CodeChunk(file_path, language, start_line, end_line, symbol, text)]

    overlap = settings.chunk_overlap_lines
    out: list[CodeChunk] = []
    i = 0
    part = 1
    while i < len(lines):
        window = lines[i:i + max_lines]
        s = start_line + i
        e = min(start_line + i + len(window) - 1, end_line)
        out.append(
            CodeChunk(file_path, language, s, e, f"{symbol} (part {part})", "\n".join(window))
        )
        i += max_lines - overlap
        part += 1
    return out


def _fixed_window_chunks(
    file_path: str, language: str, lines: list[str], max_lines: int, overlap: int
) -> list[CodeChunk]:
    chunks: list[CodeChunk] = []
    i = 0
    while i < len(lines):
        window = lines[i:i + max_lines]
        start_line = i + 1
        end_line = i + len(window)
        text = "\n".join(window)
        if text.strip():
            chunks.append(CodeChunk(file_path, language, start_line, end_line, None, text))
        i += max_lines - overlap
    return chunks


def _group_consecutive(numbers: list[int]) -> list[tuple[int, int]]:
    groups: list[tuple[int, int]] = []
    start = prev = numbers[0]
    for n in numbers[1:]:
        if n == prev + 1:
            prev = n
            continue
        groups.append((start, prev))
        start = prev = n
    groups.append((start, prev))
    return groups


def chunk_file(file_path: str, language: str | None, source: str) -> list[CodeChunk]:
    if not source.strip():
        return []
    lang = language or "text"
    if lang == "python":
        return chunk_python_file(file_path, source)
    return chunk_generic_file(file_path, lang, source)
