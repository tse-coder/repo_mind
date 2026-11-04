"""
Integration test for the LangGraph skeleton — verifies full end-to-end execution
with stub nodes and MemorySaver checkpointing.
"""

from backend.agent.graph import create_investigation_app


def test_investigation_graph_runs_to_completion(tmp_path):
    """Test that the investigation graph executes from intake to answer."""
    app = create_investigation_app()

    initial_input = {
        "repo_path": str(tmp_path),
        "query": "Where is the authentication handler defined?",
        "tool_history": [],
        "evidence_store": [],
        "findings": [],
        "reflections": [],
    }

    config = {"configurable": {"thread_id": "test_thread_001"}}
    final_state = app.invoke(initial_input, config=config)

    # Assertions on state transitions
    assert final_state["status"] in ("SUFFICIENT", "PARTIAL")
    assert final_state["commit_sha"].startswith("dir_") or len(final_state["commit_sha"]) > 0
    assert final_state["query_type"] == "LOCATE"
    assert len(final_state["plan"]) >= 1
    assert final_state["step_count"] >= 1
    assert len(final_state["tool_history"]) >= 1
    assert final_state["tool_history"][0]["tool_slug"] in ("explore_tree", "search_code", "search_symbols")
    assert len(final_state["evidence_store"]) >= 1
    assert final_state["final_answer"] is not None
    assert len(final_state["final_answer"]) > 50
