"""
End-to-end integration test for RepoMind's full LangGraph agent powered by Gemini.
"""

from pathlib import Path
import pytest

from backend.agent.graph import create_investigation_app

SAMPLE_REPO = Path(__file__).resolve().parent.parent / "fixtures" / "sample_repo"


def test_full_agent_live_investigation():
    """Run an end-to-end investigation query against sample_repo with real LLM reasoning."""
    app = create_investigation_app()

    initial_input = {
        "repo_path": str(SAMPLE_REPO),
        "query": "Where is the login handler defined in this repository?",
        "max_steps": 2,  # Budget-capped for fast test execution
        "tool_history": [],
        "evidence_store": [],
        "findings": [],
        "reflections": [],
    }

    config = {"configurable": {"thread_id": "test_live_investigation_001"}}
    final_state = app.invoke(initial_input, config=config)

    # 1. State assertions
    assert final_state["status"] in ("SUFFICIENT", "PARTIAL")
    assert final_state["step_count"] >= 1
    assert len(final_state["tool_history"]) >= 1

    # 2. Planning and classification
    assert final_state["query_type"] in ("LOCATE", "TRACE_FLOW", "MIXED")
    assert len(final_state["plan"]) >= 1

    # 3. Final answer quality
    final_answer = final_state.get("final_answer", "")
    assert len(final_answer) > 50
    assert any(term in final_answer.lower() for term in ["login", "auth", "handler", "router"])
