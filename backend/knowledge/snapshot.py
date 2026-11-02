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
    path = Path(repo_path).resolve()
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Repository path does not exist or is not a directory: {path}")

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
