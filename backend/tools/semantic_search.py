"""
semantic_search tool — Concept-to-code retrieval using local ChromaDB and FastEmbed embeddings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from backend.knowledge.snapshot import get_snapshot_info
from backend.knowledge.vector_store import RepoVectorStore, chunk_file_by_lines
from backend.tools.explore_tree import DEFAULT_EXCLUDED_DIRS


def semantic_search(
    repo_path: str,
    query: str,
    k: int = 5,
    path_scope: Optional[str] = None,
) -> dict[str, Any]:
    """Search repository code using natural language semantic similarity."""
    root = Path(repo_path).resolve()
    snap_info = get_snapshot_info(root)
    vector_store = RepoVectorStore(snapshot_id=snap_info.snapshot_id)

    # Index on-demand if collection is empty
    if not vector_store.is_indexed():
        all_chunks = []
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            parts = file_path.parts
            if any(p.startswith(".") or p in DEFAULT_EXCLUDED_DIRS for p in parts):
                continue
            # Focus on text / code files
            if file_path.suffix in (".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ts", ".js"):
                chunks = chunk_file_by_lines(file_path=file_path, repo_root=root)
                all_chunks.extend(chunks)

        if all_chunks:
            vector_store.index_chunks(all_chunks)

    results = vector_store.search(query=query, top_k=k, path_scope=path_scope)

    chunks_data = [
        {
            "file_path": c.file_path,
            "start_line": c.start_line,
            "end_line": c.end_line,
            "score": round(c.score, 4),
            "snippet": c.content,
        }
        for c in results
    ]

    return {
        "status": "SUCCESS",
        "query": query,
        "k": k,
        "result_count": len(chunks_data),
        "results": chunks_data,
    }
