"""
policy_check_node — Validates tool calls against the Policy Gateway.

Ensures path confinement, tool allowlist, and budget limits.
"""

from backend.agent.state import InvestigationState


# Allowlisted tool slugs
ALLOWED_TOOLS = frozenset({
    # Execution tools
    "explore_tree", "read_file", "search_code",
    "search_symbols", "get_symbol", "find_references",
    "get_relationships", "trace_calls", "semantic_search", "get_history",
    # Meta-tools
    "update_plan", "record_finding", "reflect_on_findings", "request_clarification",
})


def policy_check_node(state: InvestigationState) -> dict:
    """Validate the proposed tool call against policy rules.

    Checks:
    1. Tool slug is in the allowlist.
    2. Budget (step_count) has not been exceeded.

    Full path confinement and secret redaction are added in Phase 3.

    Returns the tool call unchanged if valid, or marks it as POLICY_DENIED.
    """
    tool_call = state["current_tool_call"]
    if tool_call is None:
        return {
            "current_tool_call": {
                "tool_slug": "none",
                "arguments": {},
                "rationale": "No tool call proposed.",
                "policy_status": "DENIED",
                "denial_reason": "No tool call was provided.",
            }
        }

    tool_slug = tool_call.get("tool_slug", "")

    # Check allowlist
    if tool_slug not in ALLOWED_TOOLS:
        return {
            "current_tool_call": {
                **tool_call,
                "policy_status": "DENIED",
                "denial_reason": f"Tool '{tool_slug}' is not in the allowlist.",
            }
        }

    # Check budget
    if state["step_count"] > state["max_steps"]:
        return {
            "current_tool_call": {
                **tool_call,
                "policy_status": "DENIED",
                "denial_reason": "Step budget exhausted.",
            }
        }

    # Approved
    return {
        "current_tool_call": {
            **tool_call,
            "policy_status": "APPROVED",
        }
    }
