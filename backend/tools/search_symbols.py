"""
search_symbols tool — Finds symbols by name and kind across the repository AST.
"""

from __future__ import annotations

from typing import Any

from backend.knowledge.ast_parser import RepoASTIndex


def search_symbols(
    repo_path: str,
    query: str,
    kind: str | None = None,
    max_results: int = 25,
) -> dict[str, Any]:
    """Search for classes, functions, or methods by name."""
    ast_index = RepoASTIndex(repo_path)
    symbols = ast_index.search_symbols(query=query, kind=kind)

    results = [
        {
            "name": s.name,
            "kind": s.kind,
            "file_path": s.file_path,
            "start_line": s.start_line,
            "end_line": s.end_line,
            "signature": s.signature,
            "docstring": (s.docstring[:100] + "...") if s.docstring and len(s.docstring) > 100 else s.docstring,
            "parent": s.parent,
        }
        for s in symbols[:max_results]
    ]

    return {
        "status": "SUCCESS",
        "query": query,
        "kind": kind,
        "match_count": len(results),
        "symbols": results,
    }
