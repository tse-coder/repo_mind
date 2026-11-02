"""
Vector store implementation using ChromaDB and FastEmbed for RepoMind.

Enables local, zero-cost semantic search over code chunks without external API dependencies.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import chromadb
from fastembed import TextEmbedding

from backend.config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL_NAME


@dataclass
class SemanticChunk:
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    score: float = 0.0


class RepoVectorStore:
    """Manages semantic embeddings and retrieval for a repository snapshot."""

    def __init__(self, snapshot_id: str, persist_dir: Optional[str] = None):
        self.snapshot_id = snapshot_id
        self.persist_dir = persist_dir or CHROMA_PERSIST_DIR
        self._embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)

        self._client = chromadb.PersistentClient(path=self.persist_dir)
        collection_name = f"repo_{self.snapshot_id.replace('-', '_')}"
        self.collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"snapshot_id": self.snapshot_id},
        )

    def is_indexed(self) -> bool:
        """Check if collection already contains indexed chunks."""
        return self.collection.count() > 0

    def index_chunks(self, chunks: list[SemanticChunk]):
        """Embed and add code chunks to ChromaDB."""
        if not chunks:
            return

        documents = [c.content for c in chunks]
        embeddings = list(self._embedding_model.embed(documents))
        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "file_path": c.file_path,
                "start_line": c.start_line,
                "end_line": c.end_line,
            }
            for c in chunks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=[e.tolist() for e in embeddings],
            documents=documents,
            metadatas=metadatas,
        )

    def search(self, query: str, top_k: int = 5, path_scope: Optional[str] = None) -> list[SemanticChunk]:
        """Perform semantic similarity search."""
        if self.collection.count() == 0:
            return []

        query_embedding = list(self._embedding_model.embed([query]))[0].tolist()

        where_filter = None
        if path_scope:
            where_filter = {"file_path": {"$contains": path_scope}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
        )

        chunks: list[SemanticChunk] = []
        if not results or not results["documents"] or not results["documents"][0]:
            return chunks

        docs = results["documents"][0]
        metas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else [0.0] * len(docs)
        ids = results["ids"][0] if results["ids"] else []

        for cid, doc, meta, dist in zip(ids, docs, metas, distances):
            # Chroma returns distance (lower is closer); convert to similarity score
            score = max(0.0, 1.0 - dist)
            chunks.append(
                SemanticChunk(
                    chunk_id=cid,
                    file_path=meta.get("file_path", ""),
                    start_line=meta.get("start_line", 1),
                    end_line=meta.get("end_line", 1),
                    content=doc,
                    score=score,
                )
            )

        return chunks


def chunk_file_by_lines(file_path: Path, repo_root: Path, window_size: int = 40, overlap: int = 10) -> list[SemanticChunk]:
    """Helper to chunk a text file into overlapping line windows."""
    chunks: list[SemanticChunk] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    lines = content.splitlines()
    if not lines:
        return []

    rel_path = str(file_path.relative_to(repo_root))
    step = max(1, window_size - overlap)

    for start in range(0, len(lines), step):
        end = min(start + window_size, len(lines))
        chunk_lines = lines[start:end]
        chunk_text = "\n".join(chunk_lines)

        chunk_id = hashlib.sha256(f"{rel_path}:{start}:{end}".encode()).hexdigest()[:16]
        chunks.append(
            SemanticChunk(
                chunk_id=chunk_id,
                file_path=rel_path,
                start_line=start + 1,
                end_line=end,
                content=chunk_text,
            )
        )

        if end >= len(lines):
            break

    return chunks
