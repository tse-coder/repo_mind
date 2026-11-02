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

router = APIRouter(tags=["investigation"])


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
    path_obj = Path(request.repo_path).resolve()
    if not path_obj.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository path does not exist: {request.repo_path}",
        )
    if not path_obj.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository path is not a directory: {request.repo_path}",
        )

    try:
        session = manager.create_session(
            repo_path=str(path_obj),
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
