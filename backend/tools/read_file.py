"""
read_file tool — Reads authoritative content from repository files with line ranges.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from backend.config import READ_FILE_MAX_LINES


def is_binary_file(file_path: Path) -> bool:
    """Check if file appears to be binary by inspecting initial bytes."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except OSError:
        return False


def read_file(
    repo_path: str,
    file_path: str,
    start_line: int | None = None,
    end_line: int | None = None,
    max_lines: int = READ_FILE_MAX_LINES,
) -> dict[str, Any]:
    """Read lines from a file with content hash and line range verification."""
    root = Path(repo_path).resolve()
    target = (root / file_path).resolve()

    if not target.exists() or not target.is_file():
        return {
            "status": "ERROR",
            "error": f"File '{file_path}' does not exist.",
            "file_path": file_path,
        }

    if is_binary_file(target):
        return {
            "status": "ERROR",
            "error": f"File '{file_path}' is a binary file and cannot be read as text.",
            "file_path": file_path,
        }

    try:
        raw_content = target.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {
            "status": "ERROR",
            "error": f"Failed to read file: {e}",
            "file_path": file_path,
        }

    all_lines = raw_content.splitlines()
    total_lines = len(all_lines)

    s_line = max(1, start_line) if start_line is not None else 1
    if end_line is not None:
        e_line = min(total_lines, end_line)
    else:
        e_line = min(total_lines, s_line + max_lines - 1)

    sliced = all_lines[s_line - 1 : e_line]

    numbered_lines = [f"{idx:4d} | {line}" for idx, line in enumerate(sliced, start=s_line)]
    content_hash = hashlib.sha256("\n".join(sliced).encode("utf-8")).hexdigest()[:16]

    return {
        "status": "SUCCESS",
        "file_path": file_path,
        "start_line": s_line,
        "end_line": e_line,
        "total_lines": total_lines,
        "line_count": len(sliced),
        "truncated": e_line < total_lines and end_line is None,
        "content_hash": content_hash,
        "content": "\n".join(numbered_lines),
    }
