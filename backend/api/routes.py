"""
FastAPI route definitions for RepoMind investigation endpoints.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from backend.api.manager import manager
from backend.api.models import (
    InvestigateRequest,
    InvestigateResponse,
    ResumeRequest,
    StateResponse,
)
from backend.config import PROJECT_ROOT

router = APIRouter(tags=["investigation"])


def resolve_repo_path(raw_path: str) -> Optional[Path]:
    """
    Intelligently resolve a raw repository path or folder name to an existing directory Path.
    Supports:
    1. Absolute paths (/home/user/project)
    2. Tilde paths (~/Projects/my-app)
    3. Relative paths to CWD or PROJECT_ROOT (tests/fixtures/sample_repo)
    4. Base folder names (e.g. 'sample_repo' -> searched in project or ~/Projects)
    """
    if not raw_path or not raw_path.strip():
        return None

    cleaned = raw_path.strip()
    p = Path(cleaned).expanduser()

    # 1. Direct absolute path
    if p.is_absolute() and p.exists() and p.is_dir():
        return p.resolve()

    # 2. Relative to CWD
    cwd_p = (Path.cwd() / p).resolve()
    if cwd_p.exists() and cwd_p.is_dir():
        return cwd_p

    # 3. Relative to PROJECT_ROOT
    root_p = (PROJECT_ROOT / p).resolve()
    if root_p.exists() and root_p.is_dir():
        return root_p

    # 4. Relative to User Home
    home_p = (Path.home() / p).resolve()
    if home_p.exists() and home_p.is_dir():
        return home_p

    # 5. Search for matching directory name inside PROJECT_ROOT
    folder_name = p.name
    for match in PROJECT_ROOT.rglob(folder_name):
        if match.is_dir() and not any(part.startswith(".") for part in match.parts):
            return match.resolve()

    # 6. Search for matching directory inside ~/Projects
    projects_dir = Path.home() / "Projects"
    if projects_dir.exists() and projects_dir.is_dir():
        proj_match = projects_dir / folder_name
        if proj_match.exists() and proj_match.is_dir():
            return proj_match.resolve()
        for match in projects_dir.glob(f"*/{folder_name}"):
            if match.is_dir() and not any(part.startswith(".") for part in match.parts):
                return match.resolve()

    return None


@router.get(
    "/resolve-path",
    summary="Resolve a relative path or folder name to an absolute directory path",
)
async def resolve_path_endpoint(path: str):
    """
    Given a folder name or relative path, return the verified absolute path on disk.
    """
    resolved = resolve_repo_path(path)
    if resolved:
        return {
            "input_path": path,
            "resolved_path": str(resolved),
            "exists": True,
        }
    return {
        "input_path": path,
        "resolved_path": None,
        "exists": False,
    }


@router.post(
    "/investigate",
    response_model=InvestigateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new repository investigation",
)
async def start_investigation(request: InvestigateRequest):
    """
    Validate repository path, mint an investigation ID, and schedule background investigation.
    """
    resolved_path = resolve_repo_path(request.repo_path)
    if not resolved_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository path does not exist or is not a directory: {request.repo_path}",
        )

    try:
        session = manager.create_session(
            repo_path=str(resolved_path),
            query=request.query,
            max_steps=request.max_steps,
        )
        return InvestigateResponse(
            investigation_id=session.investigation_id,
            status=session.status,
            repo_path=session.repo_path,
            query=session.query,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate investigation: {exc}",
        )


@router.get(
    "/investigate/stream/{investigation_id}",
    summary="Stream live investigation events via Server-Sent Events (SSE)",
)
async def stream_investigation(investigation_id: str):
    """
    Subscribes to real-time investigation events via SSE.
    Emits node changes, plan updates, tool executions, reflections, tokens, and final answer.
    """
    session = manager.get_session(investigation_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )

    return EventSourceResponse(
        session.subscribe(),
        media_type="text/event-stream",
    )


@router.post(
    "/investigate/resume/{investigation_id}",
    summary="Resume an interrupted investigation with user clarification",
)
async def resume_investigation(investigation_id: str, request: ResumeRequest):
    """
    Provides clarifying feedback to resume an investigation paused via clarify_node interrupt().
    """
    session = manager.get_session(investigation_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )

    if session.status != "PAUSED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Investigation '{investigation_id}' is in status '{session.status}', cannot resume.",
        )

    try:
        manager.resume_session(investigation_id, request.response)
        return {
            "status": "RESUMED",
            "investigation_id": investigation_id,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume investigation: {exc}",
        )


@router.get(
    "/investigate/{investigation_id}/state",
    response_model=StateResponse,
    summary="Get current state snapshot of an investigation",
)
async def get_investigation_state(investigation_id: str):
    """
    Fetch the latest state snapshot, plan progress, findings, and evidence for an investigation.
    """
    session = manager.get_session(investigation_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )

    state = session.state_values
    final_ans = state.get("final_answer")
    if isinstance(final_ans, list) and len(final_ans) > 0 and isinstance(final_ans[0], dict):
        final_ans = final_ans[0].get("text", str(final_ans))

    draft_ans = state.get("draft_answer")
    if isinstance(draft_ans, list) and len(draft_ans) > 0 and isinstance(draft_ans[0], dict):
        draft_ans = draft_ans[0].get("text", str(draft_ans))

    return StateResponse(
        investigation_id=session.investigation_id,
        status=session.status,
        step_count=state.get("step_count", 0),
        current_node=session.current_node,
        query=session.query,
        query_type=state.get("query_type"),
        entities=state.get("entities", []),
        plan=state.get("plan", []),
        evidence_slots=state.get("evidence_slots", {}),
        tool_history=state.get("tool_history", []),
        findings=state.get("findings", []),
        evidence_store=state.get("evidence_store", []),
        reflections=state.get("reflections", []),
        draft_answer=str(draft_ans) if draft_ans else None,
        final_answer=str(final_ans) if final_ans else None,
        limitations=state.get("limitations", []),
        clarification_prompt=session.clarification_prompt,
    )
