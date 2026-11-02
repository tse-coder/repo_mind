"""
Pydantic data schemas for RepoMind FastAPI endpoints.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = "ok"
    version: str = "0.1.0"


class InvestigateRequest(BaseModel):
    """Payload to initiate a new repository investigation."""

    repo_path: str = Field(
        ...,
        description="Path to the local repository directory to investigate.",
    )
    query: str = Field(
        ...,
        min_length=1,
        description="The user's architectural, flow-tracing, or code investigation query.",
    )
    max_steps: int | None = Field(
        None,
        ge=1,
        le=50,
        description="Optional upper bound on tool execution steps (defaults to 5).",
    )


class InvestigateResponse(BaseModel):
    """Response returned upon successfully queueing an investigation."""

    investigation_id: str
    status: str
    repo_path: str
    query: str


class ResumeRequest(BaseModel):
    """Payload to provide clarification and resume an interrupted investigation."""

    response: str = Field(
        ...,
        min_length=1,
        description="User's clarifying response to unblock the agent.",
    )


class StateResponse(BaseModel):
    """Full snapshot of an investigation's current state."""

    investigation_id: str
    status: str
    step_count: int
    current_node: str | None = None
    query: str
    query_type: str | None = None
    entities: list[str] = []
    plan: list[dict[str, Any]] = []
    evidence_slots: dict[str, str] = {}
    tool_history: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    evidence_store: list[dict[str, Any]] = []
    reflections: list[dict[str, Any]] = []
    draft_answer: str | None = None
    final_answer: str | None = None
    limitations: list[str] = []
    clarification_prompt: dict[str, Any] | None = None
