"""
get_symbol tool — Retrieves detailed definition information for a specific symbol.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from backend.knowledge.ast_parser import RepoASTIndex


def get_symbol(
    repo_path: str,
    symbol_name: str,
    file_path: Optional[str] = None,
) -> dict[str, Any]:
    """Retrieve the exact signature, docstring, and definition range for a symbol."""
    ast_index = RepoASTIndex(repo_path)
    sym = ast_index.get_symbol(symbol_name=symbol_name, file_path=file_path)

    if not sym:
        return {
            "status": "NOT_FOUND",
            "error": f"Symbol '{symbol_name}' was not found in the repository.",
            "symbol": None,
        }

    # Read the full source lines of the symbol
    root = Path(repo_path).resolve()
    target_file = root / sym.file_path
    definition_source = ""
    if target_file.exists():
        try:
            lines = target_file.read_text(encoding="utf-8", errors="replace").splitlines()
            s_idx = max(0, sym.start_line - 1)
            e_idx = min(len(lines), sym.end_line)
            definition_source = "\n".join(lines[s_idx:e_idx])
        except OSError:
            pass

    return {
        "status": "SUCCESS",
        "symbol": {
            "name": sym.name,
            "kind": sym.kind,
            "file_path": sym.file_path,
            "start_line": sym.start_line,
            "end_line": sym.end_line,
            "signature": sym.signature,
            "docstring": sym.docstring,
            "parent": sym.parent,
            "definition_source": definition_source,
        },
    }
