"""
Snapshot identity resolver for RepoMind.

Resolves an immutable snapshot identity for a local repository or directory:
- If a .git directory exists, pins to the current commit SHA (git rev-parse HEAD).
- If not a git repo, computes a content hash of the directory structure.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

from backend.config import PROJECT_ROOT


def resolve_repo_path(raw_path: str | Path | None) -> Path | None:
    """
    Intelligently resolve a raw repository path or folder name to an existing directory Path.
    Supports:
    1. Absolute paths (/home/user/project)
    2. Tilde paths (~/Projects/my-app)
    3. Relative paths to CWD or PROJECT_ROOT (tests/fixtures/sample_repo)
    4. Sibling paths in parent directory (../apex-book or apex-book inside ~/Projects)
    5. Folder name lookup in ~/Projects or PROJECT_ROOT
    """
    if raw_path is None:
        return None

    cleaned = str(raw_path).strip()
    if not cleaned:
        return None

    p = Path(cleaned).expanduser()

    # 1. Direct absolute path
    if p.is_absolute() and p.exists() and p.is_dir():
        return p.resolve()

    # 2. Relative to CWD
    cwd_p = (Path.cwd() / p).resolve()
    if cwd_p.exists() and cwd_p.is_dir():
        return cwd_p

    # 3. Relative to PROJECT_ROOT
    root_p = (PROJECT_ROOT / p).resolve()
    if root_p.exists() and root_p.is_dir():
        return root_p

    # 4. Relative to PROJECT_ROOT.parent (e.g. sibling folders like ../apex-book)
    sibling_p = (PROJECT_ROOT.parent / p).resolve()
    if sibling_p.exists() and sibling_p.is_dir():
        return sibling_p

    # 5. Relative to User Home
    home_p = (Path.home() / p).resolve()
    if home_p.exists() and home_p.is_dir():
        return home_p

    # 6. Sibling directory match in PROJECT_ROOT.parent / folder_name
    folder_name = p.name
    parent_match = PROJECT_ROOT.parent / folder_name
    if parent_match.exists() and parent_match.is_dir():
        return parent_match.resolve()

    # 7. Search in ~/Projects / folder_name
    projects_dir = Path.home() / "Projects"
    if projects_dir.exists() and projects_dir.is_dir():
        proj_match = projects_dir / folder_name
        if proj_match.exists() and proj_match.is_dir():
            return proj_match.resolve()
        for match in projects_dir.glob(f"*/{folder_name}"):
            if match.is_dir() and not any(part.startswith(".") for part in match.parts):
                return match.resolve()

    # 8. Search for matching directory name inside PROJECT_ROOT
    for match in PROJECT_ROOT.rglob(folder_name):
        if match.is_dir() and not any(part.startswith(".") for part in match.parts):
            return match.resolve()

    return None


@dataclass(frozen=True)
class SnapshotInfo:
    """Immutable metadata about the repository snapshot."""

    repo_path: str
    snapshot_id: str
    is_git: bool
    commit_sha: str | None = None
    branch_name: str | None = None


def get_snapshot_info(repo_path: str | Path) -> SnapshotInfo:
    """Resolve the snapshot identity for a local path."""
    path = resolve_repo_path(repo_path)
    if not path or not path.exists() or not path.is_dir():
        raise ValueError(f"Repository path does not exist or is not a directory: {repo_path}")

    git_dir = path / ".git"
    if git_dir.exists():
        try:
            # 1. Get current commit SHA
            sha_proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if sha_proc.returncode == 0 and sha_proc.stdout.strip():
                commit_sha = sha_proc.stdout.strip()

                # Get branch name (or 'detached')
                branch_proc = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=path,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                branch_name = branch_proc.stdout.strip() if branch_proc.returncode == 0 else "unknown"

                return SnapshotInfo(
                    repo_path=str(path),
                    snapshot_id=commit_sha[:12],
                    is_git=True,
                    commit_sha=commit_sha,
                    branch_name=branch_name,
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Fallback for non-git directory: hash file paths and sizes
    file_signatures: list[str] = []
    for p in sorted(path.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            try:
                rel = p.relative_to(path)
                file_signatures.append(f"{rel}:{p.stat().st_size}")
            except OSError:
                continue

    digest = hashlib.sha256("\n".join(file_signatures).encode("utf-8")).hexdigest()
    snapshot_id = f"dir_{digest[:12]}"

    return SnapshotInfo(
        repo_path=str(path),
        snapshot_id=snapshot_id,
        is_git=False,
    )
