"""
search_docs tool — Architectural intent RAG over READMEs, docs/, ADRs, and RFCs.

Indexes documentation into a dedicated Chroma collection (separate from code
embeddings) using heading-aware chunks so "why" questions retrieve design
rationale rather than implementation fragments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.knowledge.docs_index import chunk_markdown_by_headings, discover_doc_files
from backend.knowledge.snapshot import get_snapshot_info
from backend.knowledge.vector_store import RepoVectorStore


def search_docs(
    repo_path: str,
    query: str,
    k: int = 5,
    path_scope: str | None = None,
) -> dict[str, Any]:
    """Retrieve documentation and ADR sections by semantic similarity."""
    root = Path(repo_path).resolve()
    snap_info = get_snapshot_info(root)
    vector_store = RepoVectorStore(
        snapshot_id=snap_info.snapshot_id,
        collection_prefix="docs",
    )

    if not vector_store.is_indexed():
        all_chunks = []
        for file_path in discover_doc_files(root):
            all_chunks.extend(chunk_markdown_by_headings(file_path, root))
        if all_chunks:
            vector_store.index_chunks(all_chunks)

    if vector_store.collection.count() == 0:
        return {
            "status": "SUCCESS",
            "query": query,
            "k": k,
            "result_count": 0,
            "indexed_files": 0,
            "results": [],
            "note": "No documentation files (README, docs/, ADR/, RFC) were found in this repository.",
        }

    results = vector_store.search(query=query, top_k=k, path_scope=path_scope)
    chunks_data = [
        {
            "file_path": c.file_path,
            "start_line": c.start_line,
            "end_line": c.end_line,
            "heading": c.heading,
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
