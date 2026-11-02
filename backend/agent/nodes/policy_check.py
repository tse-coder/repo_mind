"""
policy_check_node — Enforces security, path confinement, and budget limits via PolicyGateway.
"""

from backend.agent.state import InvestigationState
from backend.policy.gateway import PolicyGateway


def policy_check_node(state: InvestigationState) -> dict:
    """Validate the proposed tool call against PolicyGateway rules."""
    tool_call = state.get("current_tool_call")
    if not tool_call:
        return {
            "current_tool_call": {
                "tool_slug": "none",
                "arguments": {},
                "rationale": "No tool call proposed.",
                "policy_status": "DENIED",
                "denial_reason": "No tool call was provided.",
            }
        }

    gateway = PolicyGateway(repo_path=state["repo_path"])
    tool_slug = tool_call.get("tool_slug", "")
    arguments = tool_call.get("arguments", {})

    check_result = gateway.validate(
        tool_slug=tool_slug,
        arguments=arguments,
        step_count=state.get("step_count", 0),
        max_steps=state.get("max_steps", 25),
    )

    if not check_result.allowed:
        return {
            "current_tool_call": {
                **tool_call,
                "policy_status": "DENIED",
                "denial_reason": check_result.reason,
            }
        }

    return {
        "current_tool_call": {
            **tool_call,
            "arguments": check_result.sanitized_args or arguments,
            "policy_status": "APPROVED",
        }
    }
