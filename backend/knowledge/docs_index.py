"""
Documentation corpus discovery and heading-aware markdown chunking.

Used by the search_docs RAG tool so architectural intent (ADRs, READMEs, RFCs)
is indexed separately from source-code embeddings.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from backend.config import DEFAULT_EXCLUDED_DIRS
from backend.knowledge.vector_store import SemanticChunk

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

DOC_SUFFIXES = frozenset({".md", ".mdx", ".rst", ".txt", ".adoc"})
DOC_DIR_HINTS = frozenset({
    "docs",
    "doc",
    "adr",
    "adrs",
    "rfc",
    "rfcs",
    "design",
    "architecture",
})
ROOT_DOC_NAMES = frozenset({
    "readme.md",
    "readme.rst",
    "contributing.md",
    "architecture.md",
    "design.md",
    "changelog.md",
    "history.md",
    "adr.md",
})


def is_documentation_file(rel_path: Path) -> bool:
    """Return True if a repo-relative path should be part of the docs corpus."""
    name = rel_path.name.lower()
    if name in ROOT_DOC_NAMES:
        return True
    suffix = rel_path.suffix.lower()
    if suffix not in DOC_SUFFIXES:
        return False
    parent_names = {part.lower() for part in rel_path.parts[:-1]}
    if parent_names & DOC_DIR_HINTS:
        return True
    return suffix in {".md", ".mdx", ".rst"}


def discover_doc_files(repo_root: Path) -> list[Path]:
    """Walk the repository and collect documentation files."""
    files: list[Path] = []
    for file_path in repo_root.rglob("*"):
        if not file_path.is_file():
            continue
        parts = file_path.parts
        if any(p.startswith(".") or p in DEFAULT_EXCLUDED_DIRS for p in parts):
            continue
        try:
            rel = file_path.relative_to(repo_root)
        except ValueError:
            continue
        if is_documentation_file(rel):
            files.append(file_path)
    return sorted(files)


def chunk_markdown_by_headings(
    file_path: Path,
    repo_root: Path,
    max_chars: int = 1800,
) -> list[SemanticChunk]:
    """Split markdown/text docs on headings so each section stays intact."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    lines = text.splitlines()
    if not lines:
        return []

    rel_path = str(file_path.relative_to(repo_root))
    sections: list[tuple[str, int, int, list[str]]] = []
    heading_stack: list[tuple[int, str]] = []
    current_start = 1
    current_lines: list[str] = []
    current_heading = ""

    def flush(end_line: int) -> None:
        body = [ln for ln in current_lines if ln.strip()]
        if not body:
            return
        sections.append((current_heading, current_start, end_line, list(current_lines)))

    for idx, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            if current_lines:
                flush(idx - 1)
            level = len(match.group(1))
            title = match.group(2).strip()
            heading_stack = [(lvl, ttl) for lvl, ttl in heading_stack if lvl < level]
            heading_stack.append((level, title))
            current_heading = " > ".join(ttl for _, ttl in heading_stack)
            current_start = idx
            current_lines = [line]
        else:
            current_lines.append(line)

    flush(len(lines))

    if not sections:
        # Plain text / heading-less docs: one windowed fallback chunk set
        from backend.knowledge.vector_store import chunk_file_by_lines

        return chunk_file_by_lines(file_path, repo_root)

    chunks: list[SemanticChunk] = []
    for heading, start, end, section_lines in sections:
        body = "\n".join(section_lines).strip()
        pieces = _split_long_text(body, max_chars)
        cursor = start
        for i, piece in enumerate(pieces):
            piece_lines = piece.count("\n") + 1
            piece_end = min(end, cursor + piece_lines - 1)
            embed_text = piece
            if heading:
                embed_text = f"Heading: {heading}\nFile: {rel_path}\n\n{piece}"
            chunk_id = hashlib.sha256(
                f"docs:{rel_path}:{cursor}:{piece_end}:{i}".encode()
            ).hexdigest()[:16]
            chunks.append(
                SemanticChunk(
                    chunk_id=chunk_id,
                    file_path=rel_path,
                    start_line=cursor,
                    end_line=piece_end,
                    content=embed_text,
                    heading=heading,
                )
            )
            cursor = piece_end + 1

    return chunks


def _split_long_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    paragraphs = re.split(r"\n\s*\n", text)
    pieces: list[str] = []
    buf = ""
    for para in paragraphs:
        candidate = f"{buf}\n\n{para}".strip() if buf else para
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            pieces.append(buf)
        if len(para) <= max_chars:
            buf = para
        else:
            for i in range(0, len(para), max_chars):
                pieces.append(para[i : i + max_chars])
            buf = ""
    if buf:
        pieces.append(buf)
    return pieces or [text[:max_chars]]
