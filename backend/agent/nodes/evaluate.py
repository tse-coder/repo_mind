"""
evaluate_node — Central routing hub of the agent loop.

After each observation, assesses whether to continue investigating,
reflect on failure, reconcile contradictions, revise the plan, or synthesize.
Sets ``next_route`` to direct the conditional edge.
"""

from backend.agent.state import InvestigationState


def evaluate_node(state: InvestigationState) -> dict:
    """Evaluate current state and decide the next branch.

    Routes to one of:
      - "select_action"  — more evidence needed, continue the loop
      - "plan"           — plan needs revision
      - "reflect"        — tool failure or empty results
      - "reconcile"      — contradictory findings detected
      - "synthesize"     — sufficient evidence or budget/strategy exhausted
      - "clarify"        — blocking ambiguity requiring user input

    Stub: routes to 'synthesize' after the first tool call to short-circuit
    the loop for skeleton testing. Phase 4 replaces with full logic.
    """
    step_count = state["step_count"]
    max_steps = state["max_steps"]
    consecutive_no_progress = state.get("consecutive_no_progress", 0)

    # ── Deterministic guards (kept in all phases) ──────────────────────────────

    # Budget exhausted
    if step_count >= max_steps:
        return {
            "next_route": "synthesize",
            "status": "PARTIAL",
            "limitations": state.get("limitations", []) + ["Step budget exhausted."],
        }

    # Anti-loop guard: 3+ consecutive steps with no new evidence
    if consecutive_no_progress >= 3:
        return {
            "next_route": "synthesize",
            "status": "PARTIAL",
            "consecutive_no_progress": 0,
            "limitations": state.get("limitations", []) + [
                "Investigation stalled — no new evidence after 3 consecutive steps."
            ],
        }

    # ── Check if all slots are resolved ────────────────────────────────────────
    slots = state.get("evidence_slots", {})
    all_resolved = all(
        s in ("SUPPORTED", "INFERRED", "UNANSWERABLE") for s in slots.values()
    )
    if all_resolved and slots:
        return {
            "next_route": "synthesize",
            "status": "SUFFICIENT",
        }

    # ── Stub: after first observation, go to synthesis ─────────────────────────
    # In the real agent (Phase 4), this checks tool results, retry ledger,
    # contradiction signals, and decides among all 8 branches.
    if step_count >= 1:
        # Mark the single slot as supported for the stub flow
        updated_slots = {k: "SUPPORTED" for k in slots}
        return {
            "next_route": "synthesize",
            "status": "SUFFICIENT",
            "evidence_slots": updated_slots,
        }

    return {
        "next_route": "select_action",
    }
