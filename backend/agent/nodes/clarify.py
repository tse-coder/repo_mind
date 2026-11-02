"""
clarify_node — Pauses the investigation for user input using LangGraph interrupt().
"""

from __future__ import annotations

from typing import Any
from langgraph.types import interrupt

from backend.agent.state import InvestigationState


def clarify_node(state: InvestigationState) -> dict:
    """Pause execution via LangGraph interrupt() to ask the user a clarifying question."""
    clarification_question = state.get("query", "Please provide more details on what you would like to investigate.")

    # Interrupt halts graph execution and checkpoints state.
    # When resumed via Command(resume=...), user_response receives the value.
    try:
        user_response = interrupt({
            "type": "clarification_request",
            "question": clarification_question,
            "clarification_count": state.get("clarification_count", 0) + 1,
        })
    except Exception:
        # Fallback if interrupt is not supported in current runner context
        user_response = "User confirmed default flow."

    return {
        "needs_clarification": False,
        "clarification_count": state.get("clarification_count", 0) + 1,
        "status": "RUNNING",
        "next_route": "plan",
    }
