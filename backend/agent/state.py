"""
InvestigationState — the single shared state object passed through every LangGraph node.

Uses TypedDict with Annotated[list, operator.add] for append-only collection fields,
so each node can return new items without clobbering previous entries.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

# ── Sub-structures ─────────────────────────────────────────────────────────────


class EvidenceItem(TypedDict):
    """A single piece of raw evidence collected from a tool result."""

    id: str
    file_path: str
    start_line: int
    end_line: int
    content_hash: str
    snippet: str
    tool_source: str
    is_direct: bool  # True = read from file; False = from search/index


class Finding(TypedDict):
    """A conclusion derived from one or more evidence items."""

    id: str
    claim: str
    evidence_ids: list[str]
    confidence: str  # "CONFIRMED" | "INFERRED" | "NOT_FOUND"
    slot_id: str


class PlanGoal(TypedDict):
    """One goal in the agent's versioned investigation plan."""

    id: str
    description: str
    status: str  # "PENDING" | "IN_PROGRESS" | "COMPLETED" | "BLOCKED"
    evidence_slot: str


class StrategyRetry(TypedDict):
    """Tracks retry attempts for a (intent, tool_family) strategy key."""

    attempts: int
    adjustments_tried: list[str]
    exhausted: bool


class ToolCallRecord(TypedDict):
    """Record of a single tool invocation."""

    step: int
    tool_slug: str
    arguments: dict[str, Any]
    rationale: str
    status: str  # "SUCCESS" | "ERROR" | "TIMEOUT" | "POLICY_DENIED"
    output_summary: str
    cached: bool


class ReflectionEntry(TypedDict):
    """A structured self-critique entry."""

    trigger: str  # What caused the reflection
    diagnosis: str  # What went wrong
    next_approach: str  # What to do differently


# ── Main State ─────────────────────────────────────────────────────────────────


class InvestigationState(TypedDict):
    """
    The complete investigation state, checkpointed by LangGraph at every node.

    Fields annotated with ``operator.add`` are append-only: a node returns new
    items in a list and LangGraph merges them into the existing list automatically.
    All other fields are overwritten by the latest node return value.
    """

    # ── Context (set once at intake) ───────────────────────────────────────────
    investigation_id: str
    repo_path: str
    commit_sha: str
    query: str
    artifact_type: str | None  # "EXPLAIN" | "ARCHITECTURE_DIAGRAM" | "DATA_FLOW" | "SCHEMA_ERD" | "API_CONTRACTS"

    # ── Classification ─────────────────────────────────────────────────────────
    query_type: str  # "LOCATE" | "TRACE_FLOW" | "ARCHITECTURE" | "DEPENDENCY" | "ERROR_ORIGIN" | "MIXED"
    entities: list[str]  # Key symbols / filenames mentioned
    needs_clarification: bool

    # ── Plan & Goals ───────────────────────────────────────────────────────────
    evidence_slots: dict[str, str]  # slot_name -> "OPEN" | "SUPPORTED" | "INFERRED" | "UNANSWERABLE"
    plan: list[PlanGoal]
    plan_version: int
    current_goal_id: str | None

    # ── Reverse-engineering stores ─────────────────────────────────────────────
    contracts_store: Annotated[list[dict[str, Any]], operator.add]
    models_store: Annotated[list[dict[str, Any]], operator.add]

    # ── Append-only stores ─────────────────────────────────────────────────────
    tool_history: Annotated[list[ToolCallRecord], operator.add]
    evidence_store: Annotated[list[EvidenceItem], operator.add]
    findings: Annotated[list[Finding], operator.add]
    reflections: Annotated[list[ReflectionEntry], operator.add]

    # ── Current tool call (ephemeral, passed between select → policy → execute → observe) ──
    current_tool_call: dict[str, Any] | None

    # ── Retry tracking ─────────────────────────────────────────────────────────
    retry_ledger: dict[str, StrategyRetry]

    # ── Budgets & Control ──────────────────────────────────────────────────────
    step_count: int
    max_steps: int
    consecutive_no_progress: int  # Anti-loop guard counter
    clarification_count: int

    # ── Results ────────────────────────────────────────────────────────────────
    draft_answer: str | None
    final_answer: str | None
    limitations: list[str]
    status: str  # "RUNNING" | "PAUSED" | "SUFFICIENT" | "PARTIAL" | "FAILED"

    # ── Routing hint (set by evaluate_node, read by conditional edges) ─────────
    next_route: str  # "select_action" | "plan" | "reflect" | "reconcile" | "synthesize" | "clarify"
