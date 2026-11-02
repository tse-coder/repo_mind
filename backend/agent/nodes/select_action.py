"""
select_action_node — Chooses the next tool call based on state.

The LLM selects a tool and arguments with a 1-sentence rationale.
"""

from backend.agent.state import InvestigationState


def select_action_node(state: InvestigationState) -> dict:
    """Select the next tool to call based on open evidence slots and budget.

    Stub: always selects ``explore_tree`` as the first action, then
    forces the loop toward synthesis on subsequent calls.
    Phase 4 replaces this with an LLM tool-selection call.
    """
    step = state["step_count"]

    # Stub: simulate a single tool call then move to synthesis
    tool_call = {
        "tool_slug": "explore_tree",
        "arguments": {"subpath": ".", "depth": 2},
        "rationale": f"[STUB] Step {step + 1}: Exploring the repository tree structure.",
    }

    return {
        "current_tool_call": tool_call,
        "step_count": step + 1,
    }
