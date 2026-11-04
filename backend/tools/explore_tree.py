"""
explore_tree tool — Navigates repository structure at configurable depth and filtering.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.config import DEFAULT_EXCLUDED_DIRS


def explore_tree(
    repo_path: str,
    subpath: str = ".",
    depth: int = 2,
    glob_pattern: str | None = None,
    max_entries: int = 100,
) -> dict[str, Any]:
    """List directory contents within the repository at given depth and pattern."""
    root = Path(repo_path).resolve()
    target = (root / subpath).resolve()

    if not target.exists() or not target.is_dir():
        return {
            "status": "ERROR",
            "error": f"Path '{subpath}' does not exist or is not a directory.",
            "entries": [],
        }

    entries: list[dict[str, Any]] = []
    truncated = False

    def _walk(current_dir: Path, current_depth: int):
        nonlocal truncated
        if current_depth > depth or len(entries) >= max_entries:
            if len(entries) >= max_entries:
                truncated = True
            return

        try:
            items = sorted(current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return

        for item in items:
            if item.name in DEFAULT_EXCLUDED_DIRS or item.name.startswith("."):
                continue

            rel = str(item.relative_to(root))
            if item.is_file():
                if glob_pattern and not item.match(glob_pattern):
                    continue
                size = item.stat().st_size if item.exists() else 0
                entries.append({
                    "path": rel,
                    "type": "file",
                    "size_bytes": size,
                    "extension": item.suffix,
                })
            elif item.is_dir():
                entries.append({
                    "path": rel,
                    "type": "directory",
                })
                _walk(item, current_depth + 1)

            if len(entries) >= max_entries:
                truncated = True
                return

    _walk(target, 1)

    return {
        "status": "SUCCESS",
        "subpath": subpath,
        "depth": depth,
        "entry_count": len(entries),
        "truncated": truncated,
        "entries": entries,
    }
