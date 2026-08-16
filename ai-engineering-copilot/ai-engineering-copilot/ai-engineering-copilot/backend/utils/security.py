"""
Security helpers.

These guard against the most relevant risks when dealing with
untrusted, user-supplied repository content:

- Path traversal when a client requests a file by path.
- Arbitrary command execution (we never `exec`/`eval`/shell out to
  anything inside a cloned repo; git clone is the only subprocess we run,
  and it runs with network-only, non-interactive flags).
- Unbounded repository size / file count (see config.max_repo_size_mb,
  config.max_indexed_files).
"""
import re
from pathlib import Path

GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(\.git)?/?$"
)


class InvalidGitHubURLError(ValueError):
    pass


class PathTraversalError(ValueError):
    pass


def parse_github_url(url: str) -> tuple[str, str]:
    """Validate a GitHub URL and extract (owner, repo). Raises InvalidGitHubURLError."""
    if not url or not isinstance(url, str):
        raise InvalidGitHubURLError("A GitHub repository URL is required.")
    match = GITHUB_URL_RE.match(url.strip())
    if not match:
        raise InvalidGitHubURLError(
            "Invalid GitHub URL. Expected format: https://github.com/<owner>/<repo>"
        )
    return match.group("owner"), match.group("repo")


def safe_join(base_dir: Path, relative_path: str) -> Path:
    """
    Safely join a user-supplied relative path onto a base directory,
    rejecting any attempt to escape the base directory (path traversal).
    """
    base_dir = base_dir.resolve()
    candidate = (base_dir / relative_path).resolve()
    if base_dir not in candidate.parents and candidate != base_dir:
        raise PathTraversalError(f"Path '{relative_path}' resolves outside the repository root.")
    return candidate
