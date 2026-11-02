"""
execute_tool_node — Dispatches the approved tool call to the actual tool implementation.

In Phase 1 this is a stub that simulates tool output.
Phase 2 wires in real tool implementations.
"""

from backend.agent.state import InvestigationState, ToolCallRecord


def execute_tool_node(state: InvestigationState) -> dict:
    """Execute the approved tool call and record the result.

    Stub: returns a placeholder result simulating a directory listing.
    Phase 2 replaces this with actual tool dispatch.
    """
    tool_call = state["current_tool_call"]
    if tool_call is None:
        return {}

    tool_slug = tool_call.get("tool_slug", "unknown")
    rationale = tool_call.get("rationale", "")

    # Stub output
    stub_output = f"[STUB OUTPUT] Tool '{tool_slug}' executed successfully with simulated results."

    record = ToolCallRecord(
        step=state["step_count"],
        tool_slug=tool_slug,
        arguments=tool_call.get("arguments", {}),
        rationale=rationale,
        status="SUCCESS",
        output_summary=stub_output,
        cached=False,
    )

    return {
        "tool_history": [record],
        "current_tool_call": {
            **tool_call,
            "output": stub_output,
            "execution_status": "SUCCESS",
        },
    }
