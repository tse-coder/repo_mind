"""
Integration tests for RepoMind FastAPI endpoints:
- Health check
- Investigation initiation and validation
- State inspection
- Real-time SSE streaming
- Clarification pause & resume
"""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from backend.api.manager import InvestigationSession, manager
from backend.main import app

SAMPLE_REPO = Path(__file__).resolve().parent.parent / "fixtures" / "sample_repo"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_health_check():
    """Verify GET /api/health returns 200 OK and version info."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


@pytest.mark.asyncio
async def test_resolve_path_endpoint():
    """Verify GET /api/resolve-path resolves relative folder names to absolute paths."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/resolve-path?path=sample_repo")
        assert res.status_code == 200
        data = res.json()
        assert data["exists"] is True
        assert data["resolved_path"].endswith("tests/fixtures/sample_repo")

        # Non-existent path
        res_nonexistent = await client.get("/api/resolve-path?path=nonexistent_xyz_dir_999")
        assert res_nonexistent.status_code == 200
        assert res_nonexistent.json()["exists"] is False


@pytest.mark.asyncio
async def test_investigate_validation_nonexistent_path():
    """Verify POST /api/investigate returns 400 when repository directory does not exist."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "repo_path": "/path/that/definitely/does/not/exist/999",
            "query": "Where is the login handler?",
        }
        response = await client.post("/api/investigate", json=payload)
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]


@pytest.mark.asyncio
async def test_investigate_validation_file_not_directory():
    """Verify POST /api/investigate returns 400 when repo_path points to a file, not a directory."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "repo_path": str(SAMPLE_REPO / "config.py"),
            "query": "Where is the config?",
        }
        response = await client.post("/api/investigate", json=payload)
        assert response.status_code == 400
        assert "not a directory" in response.json()["detail"]


@pytest.mark.asyncio
async def test_investigate_validation_empty_query():
    """Verify POST /api/investigate rejects empty queries with 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "repo_path": str(SAMPLE_REPO),
            "query": "",
        }
        response = await client.post("/api/investigate", json=payload)
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_investigate_creation_and_state():
    """Verify starting an investigation creates a session and allows state queries."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "repo_path": str(SAMPLE_REPO),
            "query": "Where is the auth service?",
            "max_steps": 2,
        }
        create_resp = await client.post("/api/investigate", json=payload)
        assert create_resp.status_code == 201
        data = create_resp.json()
        assert "investigation_id" in data
        assert data["investigation_id"].startswith("inv_")
        assert data["status"] in ("INITIALIZED", "RUNNING")

        inv_id = data["investigation_id"]

        # Fetch state snapshot
        state_resp = await client.get(f"/api/investigate/{inv_id}/state")
        assert state_resp.status_code == 200
        state_data = state_resp.json()
        assert state_data["investigation_id"] == inv_id
        assert state_data["query"] == payload["query"]
        assert "plan" in state_data
        assert "findings" in state_data


@pytest.mark.asyncio
async def test_state_not_found():
    """Verify GET /api/investigate/{id}/state returns 404 for unknown IDs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/investigate/nonexistent_xyz/state")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_stream_not_found():
    """Verify GET /api/investigate/stream/{id} returns 404 for unknown IDs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/investigate/stream/nonexistent_xyz")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stream_events_replayed():
    """Verify GET /api/investigate/stream/{id} delivers past events and live SSE format."""
    inv_id = "inv_stream_test"
    session = InvestigationSession(
        investigation_id=inv_id,
        repo_path=str(SAMPLE_REPO),
        query="Test stream query",
        max_steps=2,
    )
    session.status = "COMPLETED"
    manager._sessions[inv_id] = session

    # Populate synthetic event history
    await session.emit_event("node_change", {"node": "intake"})
    await session.emit_event("plan_update", {"plan": [{"id": "g1", "description": "Goal 1"}]})
    await session.emit_event("done", {"status": "SUFFICIENT", "final_answer": "Done."})

    transport = ASGITransport(app=app)
    async with (
        AsyncClient(transport=transport, base_url="http://test") as client,
        client.stream("GET", f"/api/investigate/stream/{inv_id}") as response,
    ):
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        events_received = []
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                events_received.append(line.split(":", 1)[1].strip())
            if len(events_received) >= 3:
                break

        assert "node_change" in events_received
        assert "plan_update" in events_received
        assert "done" in events_received


@pytest.mark.asyncio
async def test_resume_not_paused():
    """Verify POST /api/investigate/resume/{id} returns 400 if session is not paused."""
    inv_id = "inv_not_paused"
    session = InvestigationSession(
        investigation_id=inv_id,
        repo_path=str(SAMPLE_REPO),
        query="Test query",
        max_steps=2,
    )
    session.status = "RUNNING"
    manager._sessions[inv_id] = session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/investigate/resume/{inv_id}",
            json={"response": "Focus on auth_service.py"},
        )
        assert resp.status_code == 400
        assert "cannot resume" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_resume_unknown_session():
    """Verify POST /api/investigate/resume/{id} returns 404 for unknown IDs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/investigate/resume/nonexistent_xyz",
            json={"response": "test"},
        )
        assert resp.status_code == 404
