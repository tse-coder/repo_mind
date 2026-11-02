"""
get_relationships tool — Inspects import and dependency relationships for a file.
"""

from __future__ import annotations

from typing import Any
from backend.knowledge.ast_parser import RepoASTIndex


def get_relationships(
    repo_path: str,
    file_path: str,
    direction: str = "imports",
) -> dict[str, Any]:
    """Retrieve modules imported by the file or other files importing this file."""
    ast_index = RepoASTIndex(repo_path)
    rels = ast_index.get_relationships(file_path=file_path, direction=direction)

    edges = [
        {
            "source_file": r.source_file,
            "module": r.module,
            "imported_names": r.imported_names,
            "is_relative": r.is_relative,
        }
        for r in rels
    ]

    return {
        "status": "SUCCESS",
        "file_path": file_path,
        "direction": direction,
        "relationship_count": len(edges),
        "relationships": edges,
    }
