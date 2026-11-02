"""
evaluate_node — Central routing hub. Assesses state, sufficiency, and failure conditions.
"""

from __future__ import annotations

from backend.agent.state import InvestigationState
from backend.config import MAX_RETRIES_PER_STRATEGY


def evaluate_node(state: InvestigationState) -> dict:
    """Evaluate current state and decide the next branch."""
    step_count = state.get("step_count", 0)
    max_steps = state.get("max_steps", 25)
    slots = state.get("evidence_slots", {})
    history = state.get("tool_history", [])
    last_call = history[-1] if history else None
    limitations = list(state.get("limitations", []))

    # 1. Budget guard
    if step_count >= max_steps:
        limitations.append(f"Step budget reached ({step_count}/{max_steps}). Proceeding to synthesis with partial findings.")
        return {
            "next_route": "synthesize",
            "status": "PARTIAL",
            "limitations": limitations,
        }

    # 2. Check last tool call for failure / timeout / policy denial
    if last_call:
        if last_call["status"] in ("ERROR", "TIMEOUT", "POLICY_DENIED"):
            return {
                "next_route": "reflect",
            }

    # 3. Check for strategy retry exhaustion
    retry_ledger = dict(state.get("retry_ledger", {}))
    if last_call:
        strategy_key = f"{last_call['tool_slug']}"
        entry = retry_ledger.get(strategy_key, {"attempts": 0, "adjustments_tried": [], "exhausted": False})

        # If last call produced no findings or evidence, increment retry
        evidence_store = state.get("evidence_store", [])
        last_produced_evidence = any(e["tool_source"] == last_call["tool_slug"] for e in evidence_store[-2:])

        if not last_produced_evidence and last_call["status"] == "SUCCESS":
            entry["attempts"] += 1
            if entry["attempts"] >= MAX_RETRIES_PER_STRATEGY:
                entry["exhausted"] = True
                limitations.append(f"Strategy for tool '{last_call['tool_slug']}' exhausted after {entry['attempts']} attempts.")
            retry_ledger[strategy_key] = entry

    # 4. Anti-loop guard: 3 consecutive steps without new findings
    consecutive_no_progress = state.get("consecutive_no_progress", 0)
    findings = state.get("findings", [])
    if len(findings) == 0 and step_count >= 4:
        consecutive_no_progress += 1
    if consecutive_no_progress >= 3:
        limitations.append("Investigation stalled: no new evidence was uncovered across consecutive steps.")
        return {
            "next_route": "synthesize",
            "status": "PARTIAL",
            "consecutive_no_progress": consecutive_no_progress,
            "limitations": limitations,
        }

    # 5. Check if all required evidence slots are resolved
    all_resolved = len(slots) > 0 and all(
        v in ("SUPPORTED", "INFERRED", "UNANSWERABLE") for v in slots.values()
    )
    if all_resolved:
        return {
            "next_route": "synthesize",
            "status": "SUFFICIENT",
            "retry_ledger": retry_ledger,
        }

    # 6. Default: continue loop
    return {
        "next_route": "select_action",
        "retry_ledger": retry_ledger,
        "consecutive_no_progress": consecutive_no_progress,
    }
