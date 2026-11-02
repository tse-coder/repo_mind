"""
Tools registry and dispatcher for RepoMind execution tools.
"""

from typing import Any, Callable

from backend.tools.explore_tree import explore_tree
from backend.tools.read_file import read_file
from backend.tools.search_code import search_code
from backend.tools.search_symbols import search_symbols
from backend.tools.get_symbol import get_symbol
from backend.tools.find_references import find_references
from backend.tools.get_relationships import get_relationships
from backend.tools.trace_calls import trace_calls
from backend.tools.semantic_search import semantic_search
from backend.tools.get_history import get_history

TOOL_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "explore_tree": explore_tree,
    "read_file": read_file,
    "search_code": search_code,
    "search_symbols": search_symbols,
    "get_symbol": get_symbol,
    "find_references": find_references,
    "get_relationships": get_relationships,
    "trace_calls": trace_calls,
    "semantic_search": semantic_search,
    "get_history": get_history,
}


def dispatch_tool(repo_path: str, tool_slug: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool by name with arguments against the given repo path."""
    if tool_slug not in TOOL_REGISTRY:
        return {
            "status": "ERROR",
            "error": f"Tool '{tool_slug}' is not registered in TOOL_REGISTRY.",
        }

    func = TOOL_REGISTRY[tool_slug]
    try:
        return func(repo_path=repo_path, **arguments)
    except TypeError as e:
        return {
            "status": "ERROR",
            "error": f"Invalid arguments for tool '{tool_slug}': {e}",
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": f"Execution failed for tool '{tool_slug}': {e}",
        }
