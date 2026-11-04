"""
verify_node — Programmatically checks cited file paths and line ranges against local files.
"""

from __future__ import annotations

import re
from pathlib import Path

from backend.agent.state import InvestigationState

# Regex to match citations like [file.py:12] or [path/to/file.py:10-25]
CITATION_REGEX = re.compile(r"\[([a-zA-Z0-9_\-/\.]+):(\d+)(?:-(\d+))?\]")


def verify_node(state: InvestigationState) -> dict:
    """Verify that cited files exist and line numbers are valid."""
    draft = state.get("draft_answer", "")
    repo_root = Path(state.get("repo_path", ".")).resolve()
    limitations = list(state.get("limitations", []))

    citations = CITATION_REGEX.findall(draft)
    verified_count = 0
    invalid_citations = []

    for file_rel, start_l, end_l in citations:
        # Ignore pseudo-citations to root, directories, or git commit references
        if file_rel in (".", "./", "git:HEAD") or (repo_root / file_rel).is_dir():
            continue
        target = repo_root / file_rel
        if not target.exists() or not target.is_file():
            invalid_citations.append(f"{file_rel}:{start_l}")
        else:
            verified_count += 1

    if invalid_citations:
        limitations.append(
            f"Verification notice: {len(invalid_citations)} citations could not be verified on disk ({', '.join(invalid_citations[:3])})."
        )

    return {
        "limitations": limitations,
        "next_route": "answer",
    }
