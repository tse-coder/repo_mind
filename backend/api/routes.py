"""
FastAPI route definitions for RepoMind investigation endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from backend.api.manager import manager
from backend.api.models import (
    InvestigateRequest,
    InvestigateResponse,
    ResumeRequest,
    StateResponse,
)
from backend.db.supabase import db_manager
from backend.knowledge.snapshot import resolve_repo_path
from backend.security.auth import AuthUser, get_current_user_optional, require_current_user

router = APIRouter(tags=["investigation"])


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
async def start_investigation(
    request: InvestigateRequest,
    current_user: AuthUser = Depends(get_current_user_optional),
):
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
        user_id = current_user.id if current_user.is_authenticated else None
        session = manager.create_session(
            repo_path=str(resolved_path),
            query=request.query,
            max_steps=request.max_steps,
            session_id=request.session_id,
            user_id=user_id,
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


# ── User & Chat Persistence Endpoints ──────────────────────────────────────────


class SaveChatRequest(BaseModel):
    chat_id: str
    title: str = "New Investigation"
    repo_path: str
    max_steps: int = 15
    messages: list[dict[str, Any]] = Field(default_factory=list)


@router.get("/me", summary="Get current authenticated user profile")
async def get_me(current_user: AuthUser = Depends(get_current_user_optional)):
    """Return user info for the active session."""
    return current_user


@router.get("/chat/sessions", summary="List chat sessions for the authenticated user")
async def get_user_chat_sessions(current_user: AuthUser = Depends(require_current_user)):
    """Return all persistent chat sessions for the logged in user."""
    sessions = await db_manager.list_chat_sessions(current_user.id)
    return {"sessions": sessions}


@router.post("/chat/sessions", summary="Save or update a chat session and its messages")
async def save_user_chat_session(
    payload: SaveChatRequest,
    current_user: AuthUser = Depends(get_current_user_optional),
):
    """Save or update chat session metadata and messages in PostgreSQL/Supabase."""
    user_id = current_user.id if current_user.is_authenticated else None
    await db_manager.save_chat_session(
        chat_id=payload.chat_id,
        user_id=user_id,
        title=payload.title,
        repo_path=payload.repo_path,
        max_steps=payload.max_steps,
    )

    for msg in payload.messages:
        msg_id = msg.get("id") or f"msg_{payload.chat_id}_{msg.get('role')}_{msg.get('timestamp')}"
        await db_manager.save_chat_message(
            message_id=msg_id,
            chat_id=payload.chat_id,
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            thoughts=msg.get("thoughts"),
        )

    return {"status": "ok", "chat_id": payload.chat_id}


@router.get("/chat/sessions/{chat_id}/messages", summary="Get messages for a chat session")
async def get_chat_messages(
    chat_id: str,
    current_user: AuthUser = Depends(get_current_user_optional),
):
    """Return all messages belonging to a chat session."""
    messages = await db_manager.get_chat_messages(chat_id)
    return {"chat_id": chat_id, "messages": messages}

