"""
execute_tool_node — Dispatches approved tool calls and wraps output in untrusted data frames.
"""

from backend.agent.state import InvestigationState, ToolCallRecord
from backend.policy.framing import frame_untrusted_content
from backend.tools import dispatch_tool


def execute_tool_node(state: InvestigationState) -> dict:
    """Execute the approved tool call and record the framed output."""
    tool_call = state.get("current_tool_call")
    if not tool_call:
        return {}

    tool_slug = tool_call.get("tool_slug", "unknown")
    arguments = tool_call.get("arguments", {})
    rationale = tool_call.get("rationale", "")
    repo_path = state.get("repo_path", ".")

    # Dispatch to real tool implementation
    raw_result = dispatch_tool(repo_path=repo_path, tool_slug=tool_slug, arguments=arguments)

    exec_status = "SUCCESS" if raw_result.get("status") in ("SUCCESS", None) else "ERROR"

    # Frame output safely
    file_path = arguments.get("file_path") or arguments.get("subpath") or ""
    start_l = arguments.get("start_line")
    end_l = arguments.get("end_line")
    line_range = f"{start_l}-{end_l}" if start_l and end_l else ""

    framed_output = frame_untrusted_content(
        source_tool=tool_slug,
        raw_output=raw_result,
        file_path=file_path,
        line_range=line_range,
    )

    record = ToolCallRecord(
        step=state.get("step_count", 0),
        tool_slug=tool_slug,
        arguments=arguments,
        rationale=rationale,
        status=exec_status,
        output_summary=framed_output[:250],
        cached=False,
    )

    return {
        "tool_history": [record],
        "current_tool_call": {
            **tool_call,
            "output": framed_output,
            "raw_result": raw_result,
            "execution_status": exec_status,
        },
    }
