"""
trace_data_flow tool for RepoMind.

Traces an end-to-end execution path from an entrypoint symbol down through
intermediate business logic, database queries, or external calls, formatting
the hops into an ordered sequence of steps for sequence diagrams.
"""

from __future__ import annotations

from typing import Any

from backend.knowledge.ast_parser import RepoASTIndex
from backend.knowledge.snapshot import resolve_repo_path


def trace_data_flow(
    repo_path: str,
    entry_symbol: str,
    max_depth: int = 5,
) -> dict[str, Any]:
    """
    Trace chronological execution and data flow from an entrypoint.
    """
    root = resolve_repo_path(repo_path)
    if not root or not root.exists() or not root.is_dir():
        return {
            "status": "ERROR",
            "error": f"Repository path not found: {repo_path}",
        }

    ast_index = RepoASTIndex(str(root))
    call_tree = ast_index.trace_calls(entry_symbol=entry_symbol, max_depth=max_depth)

    # Flatten the tree into an ordered execution sequence
    hops: list[dict[str, Any]] = []
    step_counter = 1

    # First hop: External Client to Entrypoint
    entry_def = ast_index.get_symbol(entry_symbol)
    hops.append({
        "step": step_counter,
        "caller": "Client",
        "callee": entry_symbol,
        "file_path": entry_def.file_path if entry_def else "unknown",
        "line_number": entry_def.start_line if entry_def else 1,
        "action": f"Request dispatched to {entry_symbol}",
    })
    step_counter += 1

    def _traverse(node: dict[str, Any], caller_name: str, current_depth: int):
        nonlocal step_counter
        if current_depth > max_depth:
            return

        for child in node.get("calls", []):
            callee_name = child["name"]
            sym = ast_index.get_symbol(callee_name)
            hops.append({
                "step": step_counter,
                "caller": caller_name,
                "callee": callee_name,
                "file_path": sym.file_path if sym else "unknown",
                "line_number": sym.start_line if sym else 1,
                "action": f"{caller_name} calls {callee_name}",
            })
            step_counter += 1
            _traverse(child, callee_name, current_depth + 1)

    _traverse(call_tree, entry_symbol, 1)

    return {
        "status": "SUCCESS",
        "entry_symbol": entry_symbol,
        "hop_count": len(hops),
        "flow_steps": hops,
    }
