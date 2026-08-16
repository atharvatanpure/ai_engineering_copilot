"""
Handles interaction with GitHub: validating URLs and cloning public
repositories to local disk. This is the ONLY module allowed to invoke
`git` as a subprocess, and it does so with a strict, non-interactive,
depth-limited, timeout-bounded command — never arbitrary shell input.
"""
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from config import get_settings
from utils.security import parse_github_url, InvalidGitHubURLError  # noqa: F401 re-export

settings = get_settings()


class RepositoryNotFoundError(Exception):
    pass


class PrivateRepositoryError(Exception):
    pass


class CloneFailedError(Exception):
    pass


class RepositoryTooLargeError(Exception):
    pass


@dataclass
class CloneResult:
    local_path: Path
    default_branch: str


def _get_default_branch(local_path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(local_path), "symbolic-ref", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        branch = result.stdout.strip()
        return branch or "main"
    except Exception:
        return "main"


def clone_repository(owner: str, repo: str) -> CloneResult:
    """
    Clone a public GitHub repository with depth=1 (no history needed for
    static analysis) into settings.repo_storage_dir/<owner>__<repo>.
    """
    url = f"https://github.com/{owner}/{repo}.git"
    dest = Path(settings.repo_storage_dir) / f"{owner}__{repo}"

    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            [
                "git", "clone",
                "--depth", "1",
                "--single-branch",
                "--no-tags",
                "--quiet",
                url,
                str(dest),
            ],
            capture_output=True,
            text=True,
            timeout=settings.clone_timeout_seconds,
            env={"GIT_TERMINAL_PROMPT": "0"},  # never hang waiting for credentials
        )
    except subprocess.TimeoutExpired as exc:
        shutil.rmtree(dest, ignore_errors=True)
        raise CloneFailedError(f"Cloning timed out after {settings.clone_timeout_seconds}s.") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").lower()
        shutil.rmtree(dest, ignore_errors=True)
        if "not found" in stderr or "does not exist" in stderr:
            raise RepositoryNotFoundError(f"Repository '{owner}/{repo}' was not found.")
        if "could not read username" in stderr or "authentication failed" in stderr or "terminal prompts disabled" in stderr:
            raise PrivateRepositoryError(
                f"Repository '{owner}/{repo}' appears to be private or requires authentication. "
                "Only public repositories are supported in this MVP."
            )
        raise CloneFailedError(f"git clone failed: {result.stderr.strip()[:500]}")

    # Enforce a max repository size after clone (best-effort, du-based).
    size_mb = _dir_size_mb(dest)
    if size_mb > settings.max_repo_size_mb:
        shutil.rmtree(dest, ignore_errors=True)
        raise RepositoryTooLargeError(
            f"Repository is {size_mb:.0f} MB, which exceeds the {settings.max_repo_size_mb} MB limit."
        )

    default_branch = _get_default_branch(dest)
    return CloneResult(local_path=dest, default_branch=default_branch)


def _dir_size_mb(path: Path) -> float:
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except OSError:
                continue
    return total / (1024 * 1024)
