"""
search_code tool — Fast lexical and regex search across repository files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from backend.config import SEARCH_MAX_RESULTS
from backend.tools.explore_tree import DEFAULT_EXCLUDED_DIRS


def search_code(
    repo_path: str,
    query: str,
    is_regex: bool = False,
    path_scope: Optional[str] = None,
    max_results: int = SEARCH_MAX_RESULTS,
) -> dict[str, Any]:
    """Search for literal text or regex patterns in repository source code."""
    root = Path(repo_path).resolve()
    target_dir = (root / path_scope).resolve() if path_scope else root

    if not target_dir.exists():
        return {
            "status": "ERROR",
            "error": f"Search scope path '{path_scope}' does not exist.",
            "matches": [],
        }

    flags = 0 if is_regex else re.IGNORECASE
    try:
        pattern = re.compile(query if is_regex else re.escape(query), flags=flags)
    except re.error as e:
        return {
            "status": "ERROR",
            "error": f"Invalid regex pattern '{query}': {e}",
            "matches": [],
        }

    matches: list[dict[str, Any]] = []

    for file_path in target_dir.rglob("*"):
        if not file_path.is_file():
            continue

        parts = file_path.parts
        if any(p.startswith(".") or p in DEFAULT_EXCLUDED_DIRS for p in parts):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = content.splitlines()
        rel_path = str(file_path.relative_to(root))

        for line_idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                # Context lines (1 before, 1 after)
                ctx_start = max(0, line_idx - 2)
                ctx_end = min(len(lines), line_idx + 1)
                context = lines[ctx_start:ctx_end]

                matches.append({
                    "file_path": rel_path,
                    "line_number": line_idx,
                    "line": line.strip(),
                    "context": context,
                })

                if len(matches) >= max_results:
                    break

        if len(matches) >= max_results:
            break

    return {
        "status": "SUCCESS",
        "query": query,
        "is_regex": is_regex,
        "match_count": len(matches),
        "matches": matches,
    }
