"""
clarify_node — Pauses the investigation to ask the user a clarifying question.

Uses LangGraph's interrupt() to checkpoint state and wait for user input.
"""

from backend.agent.state import InvestigationState


def clarify_node(state: InvestigationState) -> dict:
    """Pause the investigation and request clarification from the user.

    In the live system, this calls ``langgraph.types.interrupt()``
    to halt execution and send a question to the frontend.
    The graph resumes when the user replies via ``Command(resume=...)``.

    Stub: marks the query as no longer needing clarification and continues.
    """
    return {
        "needs_clarification": False,
        "clarification_count": state["clarification_count"] + 1,
        "status": "RUNNING",
        "next_route": "plan",
    }
