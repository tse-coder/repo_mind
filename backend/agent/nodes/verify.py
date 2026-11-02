"""
verify_node — Checks every citation in the draft answer against actual evidence.

Programmatically verifies that cited file paths and line ranges match
evidence items in the store. Unsupported claims are removed or downgraded.
"""

from backend.agent.state import InvestigationState


def verify_node(state: InvestigationState) -> dict:
    """Verify the draft answer's citations against collected evidence.

    Stub: passes the draft through unchanged.
    Phase 4 replaces with programmatic file:line verification.

    Sets next_route to:
      - "answer" if verification passes or budget is exhausted
      - "select_action" if missing citations need one more lookup (budget permitting)
    """
    return {
        "next_route": "answer",
    }
