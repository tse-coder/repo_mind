"""
trace_calls tool — Recursively traces static function and method invocations from an entrypoint.
"""

from __future__ import annotations

from typing import Any
from backend.knowledge.ast_parser import RepoASTIndex


def trace_calls(
    repo_path: str,
    entry_symbol: str,
    depth: int = 3,
) -> dict[str, Any]:
    """Build a static call tree starting from an entry function or method."""
    ast_index = RepoASTIndex(repo_path)
    call_tree = ast_index.trace_calls(entry_symbol=entry_symbol, max_depth=depth)

    return {
        "status": "SUCCESS",
        "entry_symbol": entry_symbol,
        "depth": depth,
        "call_tree": call_tree,
    }
