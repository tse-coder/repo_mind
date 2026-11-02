"""
find_references tool — Locates all invocations and usages of a symbol across repository code.
"""

from __future__ import annotations

from typing import Any
from backend.knowledge.ast_parser import RepoASTIndex


def find_references(
    repo_path: str,
    symbol_name: str,
    max_results: int = 50,
) -> dict[str, Any]:
    """Find files and lines where the symbol is called or referenced."""
    ast_index = RepoASTIndex(repo_path)
    refs = ast_index.find_references(symbol_name)

    results = [
        {
            "caller_name": r.caller_name,
            "callee_name": r.callee_name,
            "file_path": r.file_path,
            "line_number": r.line_number,
        }
        for r in refs[:max_results]
    ]

    return {
        "status": "SUCCESS",
        "symbol_name": symbol_name,
        "reference_count": len(results),
        "references": results,
    }
