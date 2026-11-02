"""
reflect_node — Structured self-critique after tool failure or empty results.

Implements the Reflexion pattern: diagnose what went wrong,
hypothesize why, and propose a concrete changed approach.
"""

from backend.agent.state import InvestigationState, ReflectionEntry


def reflect_node(state: InvestigationState) -> dict:
    """Generate a reflection on the last failed or unproductive step.

    Stub: produces a generic reflection and routes back to select_action.
    Phase 4 replaces with LLM-driven diagnosis.
    """
    tool_history = state.get("tool_history", [])
    last_tool = tool_history[-1] if tool_history else None

    trigger = "tool_failure"
    diagnosis = "Unknown failure."
    next_approach = "Try a different tool or broaden the query."

    if last_tool:
        trigger = f"{last_tool['tool_slug']} returned {last_tool['status']}"
        diagnosis = f"Tool '{last_tool['tool_slug']}' did not produce useful evidence."
        next_approach = "Adjust query parameters or switch to an alternative retrieval method."

    reflection = ReflectionEntry(
        trigger=trigger,
        diagnosis=diagnosis,
        next_approach=next_approach,
    )

    return {
        "reflections": [reflection],
        "next_route": "select_action",
    }
