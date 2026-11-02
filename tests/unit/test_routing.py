"""
Unit tests for LangGraph conditional edge routing functions and evaluate_node logic.
"""

import pytest
from backend.agent.graph import (
    route_classify,
    route_select_action,
    route_policy,
    route_evaluate,
    route_verify,
)
from backend.agent.nodes.evaluate import evaluate_node


def test_route_classify_when_needs_clarification():
    state = {"needs_clarification": True}
    assert route_classify(state) == "clarify"


def test_route_classify_normal():
    state = {"needs_clarification": False}
    assert route_classify(state) == "plan"


def test_route_select_action_policy_check():
    state = {"next_route": "select_action", "current_tool_call": {"tool_slug": "read_file"}}
    assert route_select_action(state) == "policy_check"


def test_route_select_action_synthesize():
    state = {"next_route": "synthesize", "current_tool_call": None}
    assert route_select_action(state) == "synthesize"


def test_route_policy_approved():
    state = {"current_tool_call": {"policy_status": "APPROVED"}}
    assert route_policy(state) == "execute_tool"


def test_route_policy_denied():
    state = {"current_tool_call": {"policy_status": "DENIED"}}
    assert route_policy(state) == "observe"


def test_route_evaluate():
    for route in ["select_action", "plan", "reflect", "reconcile", "synthesize", "clarify"]:
        state = {"next_route": route}
        assert route_evaluate(state) == route

    # Invalid route defaults to select_action
    state = {"next_route": "unknown_branch"}
    assert route_evaluate(state) == "select_action"


def test_route_verify():
    assert route_verify({"next_route": "answer"}) == "answer"
    assert route_verify({"next_route": "select_action"}) == "select_action"


def test_evaluate_node_budget_exhausted():
    state = {
        "step_count": 25,
        "max_steps": 25,
        "consecutive_no_progress": 0,
        "evidence_slots": {"slot1": "OPEN"},
        "limitations": [],
    }
    result = evaluate_node(state)
    assert result["next_route"] == "synthesize"
    assert result["status"] == "PARTIAL"
    assert any("budget" in lim.lower() for lim in result["limitations"])


def test_evaluate_node_anti_loop_guard():
    state = {
        "step_count": 5,
        "max_steps": 25,
        "consecutive_no_progress": 3,
        "evidence_slots": {"slot1": "OPEN"},
        "limitations": [],
    }
    result = evaluate_node(state)
    assert result["next_route"] == "synthesize"
    assert result["status"] == "PARTIAL"
    assert any("stalled" in lim.lower() for lim in result["limitations"])


def test_evaluate_node_all_slots_resolved():
    state = {
        "step_count": 2,
        "max_steps": 25,
        "consecutive_no_progress": 0,
        "evidence_slots": {"slot1": "SUPPORTED", "slot2": "INFERRED"},
    }
    result = evaluate_node(state)
    assert result["next_route"] == "synthesize"
    assert result["status"] == "SUFFICIENT"
