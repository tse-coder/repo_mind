"""
RepoMind LangGraph Engine — Assembles the complete StateGraph for repository investigation.

Defines all nodes, edges, conditional branches, and checkpointing.
"""

from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from backend.agent.nodes.answer import answer_node
from backend.agent.nodes.clarify import clarify_node
from backend.agent.nodes.classify import classify_node
from backend.agent.nodes.evaluate import evaluate_node
from backend.agent.nodes.execute_tool import execute_tool_node
from backend.agent.nodes.intake import intake_node
from backend.agent.nodes.observe import observe_node
from backend.agent.nodes.plan import plan_node
from backend.agent.nodes.policy_check import policy_check_node
from backend.agent.nodes.reconcile import reconcile_node
from backend.agent.nodes.reflect import reflect_node
from backend.agent.nodes.select_action import select_action_node
from backend.agent.nodes.synthesize import synthesize_node
from backend.agent.nodes.verify import verify_node
from backend.agent.state import InvestigationState

# ── Conditional Routing Functions ──────────────────────────────────────────────


def route_classify(state: InvestigationState) -> Literal["clarify", "plan"]:
    """Route after classification: pause for clarification if ambiguous, else plan."""
    if state.get("needs_clarification", False):
        return "clarify"
    return "plan"


def route_select_action(state: InvestigationState) -> Literal["policy_check", "synthesize"]:
    """Route after action selection: proceed to policy check, or straight to synthesis if finished."""
    if state.get("next_route") == "synthesize" or not state.get("current_tool_call"):
        return "synthesize"
    return "policy_check"


def route_policy(state: InvestigationState) -> Literal["execute_tool", "observe"]:
    """Route after policy check: proceed to execution if approved, else observe error."""
    tool_call = state.get("current_tool_call") or {}
    if tool_call.get("policy_status") == "DENIED":
        return "observe"
    return "execute_tool"


def route_evaluate(
    state: InvestigationState,
) -> Literal["select_action", "plan", "reflect", "reconcile", "synthesize", "clarify"]:
    """Route out of evaluation based on next_route hint set by evaluate_node."""
    next_route = state.get("next_route", "select_action")
    valid_routes = {"select_action", "plan", "reflect", "reconcile", "synthesize", "clarify"}
    if next_route in valid_routes:
        return next_route  # type: ignore
    return "select_action"


def route_verify(state: InvestigationState) -> Literal["select_action", "answer"]:
    """Route after verification: retry loop if missing evidence, else format final answer."""
    next_route = state.get("next_route", "answer")
    if next_route == "select_action":
        return "select_action"
    return "answer"


# ── Graph Builder ──────────────────────────────────────────────────────────────


def build_investigation_graph():
    """Build and wire the uncompiled StateGraph for repository investigation."""
    workflow = StateGraph(InvestigationState)

    # 1. Register all nodes
    workflow.add_node("intake", intake_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("select_action", select_action_node)
    workflow.add_node("policy_check", policy_check_node)
    workflow.add_node("execute_tool", execute_tool_node)
    workflow.add_node("observe", observe_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("reflect", reflect_node)
    workflow.add_node("reconcile", reconcile_node)
    workflow.add_node("synthesize", synthesize_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("answer", answer_node)

    # 2. Add sequential edges
    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "classify")
    workflow.add_edge("clarify", "plan")
    workflow.add_edge("plan", "select_action")
    workflow.add_edge("execute_tool", "observe")
    workflow.add_edge("observe", "evaluate")
    workflow.add_edge("reflect", "select_action")
    workflow.add_edge("reconcile", "select_action")
    workflow.add_edge("synthesize", "verify")
    workflow.add_edge("answer", END)

    # 3. Add conditional edges
    workflow.add_conditional_edges(
        "classify",
        route_classify,
        {
            "clarify": "clarify",
            "plan": "plan",
        },
    )

    workflow.add_conditional_edges(
        "select_action",
        route_select_action,
        {
            "policy_check": "policy_check",
            "synthesize": "synthesize",
        },
    )

    workflow.add_conditional_edges(
        "policy_check",
        route_policy,
        {
            "execute_tool": "execute_tool",
            "observe": "observe",
        },
    )

    workflow.add_conditional_edges(
        "evaluate",
        route_evaluate,
        {
            "select_action": "select_action",
            "plan": "plan",
            "reflect": "reflect",
            "reconcile": "reconcile",
            "synthesize": "synthesize",
            "clarify": "clarify",
        },
    )

    workflow.add_conditional_edges(
        "verify",
        route_verify,
        {
            "select_action": "select_action",
            "answer": "answer",
        },
    )

    return workflow


def create_investigation_app(checkpointer=None):
    """Compile the investigation graph with an optional checkpointer."""
    workflow = build_investigation_graph()
    if checkpointer is None:
        checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)
