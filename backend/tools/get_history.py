"""
get_history tool — Retrieves git commit history and changes for files in the repository.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from backend.knowledge.snapshot import get_snapshot_info


def get_history(
    repo_path: str,
    file_path: str | None = None,
    max_commits: int = 10,
) -> dict[str, Any]:
    """Retrieve recent git commit log for the repository or a specific file."""
    root = Path(repo_path).resolve()
    snap = get_snapshot_info(root)

    if not snap.is_git:
        return {
            "status": "UNAVAILABLE",
            "message": "Repository is not a Git repository; commit history is unavailable.",
            "commits": [],
        }

    cmd = [
        "git",
        "log",
        f"-n{max_commits}",
        "--pretty=format:%H|%an|%ad|%s",
        "--date=short",
    ]
    if file_path:
        cmd.extend(["--", file_path])

    try:
        proc = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if proc.returncode != 0:
            return {
                "status": "ERROR",
                "error": proc.stderr.strip() or "Failed to read git history.",
                "commits": [],
            }

        commits = []
        for line in proc.stdout.splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                sha, author, date, msg = parts
                commits.append({
                    "sha": sha[:10],
                    "author": author,
                    "date": date,
                    "message": msg,
                })

        return {
            "status": "SUCCESS",
            "file_path": file_path,
            "commit_count": len(commits),
            "commits": commits,
        }
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "commits": [],
        }
