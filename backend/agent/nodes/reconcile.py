"""
reconcile_node — Handles contradictory evidence.

When two findings conflict, this node applies the authority order
(executed code > config > tests > docs) and attempts resolution.
"""

from backend.agent.state import InvestigationState


def reconcile_node(state: InvestigationState) -> dict:
    """Attempt to reconcile contradictory findings.

    Stub: logs the contradiction and routes back to select_action.
    Phase 4 replaces with LLM-driven resolution using authority ordering.
    """
    return {
        "next_route": "select_action",
    }
