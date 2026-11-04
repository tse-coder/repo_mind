"""
plan_node — Creates or revises an investigation plan based on open evidence slots.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field, model_validator

from backend.agent.llm import get_llm
from backend.agent.state import InvestigationState, PlanGoal
from backend.config import LLM_PROVIDER


class PlannedGoalItem(BaseModel):
    description: str = Field(description="Actionable goal statement for this investigation step.")
    evidence_slot: str = Field(default="primary_answer", description="The evidence slot this goal will help satisfy.")

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return {"description": str(data), "evidence_slot": "primary_answer"}
        if "description" not in data:
            for alias in ("goal", "title", "name", "action", "step"):
                if alias in data and isinstance(data[alias], str):
                    data["description"] = data[alias]
                    break
        if "evidence_slot" not in data:
            for alias in ("slot", "target_slot", "slot_id"):
                if alias in data and isinstance(data[alias], str):
                    data["evidence_slot"] = data[alias]
                    break
            if "evidence_slot" not in data:
                data["evidence_slot"] = "primary_answer"
        return data


class PlanProposal(BaseModel):
    goals: list[PlannedGoalItem] = Field(default_factory=list, description="Ordered list of investigation sub-goals.")
    revision_reason: str = Field(default="", description="If revising an existing plan, explanation of why.")

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        for key in ("PlanProposal", "proposal"):
            if key in data and isinstance(data[key], dict):
                data = data[key]
                break
        if "goals" not in data:
            for alias in ("plan", "steps", "subgoals", "sub_goals", "items"):
                if alias in data and isinstance(data[alias], list):
                    data["goals"] = data[alias]
                    break
        return data


PLAN_PROMPT = """You are a software investigation planner.
Based on the user's question, query type, and open evidence slots, generate a concise, ordered list of 1 to 4 investigation goals.
Each goal should be tied to an open evidence slot.
Focus on finding concrete code definitions, usages, or flow steps using read-only tools.
For ARCHITECTURE or "why was this designed this way" questions, include a goal that uses search_docs against README, docs/, and ADR records.
Return your proposal strictly as a JSON object adhering to the PlanProposal schema.
"""


def plan_node(state: InvestigationState) -> dict:
    """Create or revise the investigation plan."""
    query = state.get("query", "")
    query_type = state.get("query_type", "LOCATE")
    slots = state.get("evidence_slots", {})
    open_slots = [k for k, v in slots.items() if v == "OPEN"]
    existing_plan = state.get("plan", [])

    if not open_slots:
        return {"next_route": "synthesize"}

    llm = get_llm(temperature=0.0)
    structured_llm = (
        llm.with_structured_output(PlanProposal, method="json_mode")
        if LLM_PROVIDER == "groq"
        else llm.with_structured_output(PlanProposal)
    )

    chat_history = state.get("chat_history", [])
    history_ctx = ""
    if len(chat_history) > 1:
        past = [
            f"{m['role'].upper()}: {m['content'][:250]}"
            for m in chat_history[:-1][-3:]
        ]
        history_ctx = "Prior Conversation:\n" + "\n".join(past) + "\n"

    prompt_context = f"""
{history_ctx}Query: {query}
Type: {query_type}
Open Evidence Slots: {', '.join(open_slots)}
Existing Plan Goals: {[g['description'] for g in existing_plan]}
"""
    try:
        proposal: PlanProposal = structured_llm.invoke([
            ("system", PLAN_PROMPT),
            ("human", prompt_context),
        ])

        plan_goals: list[PlanGoal] = []
        for item in proposal.goals:
            plan_goals.append(
                PlanGoal(
                    id=f"goal_{uuid.uuid4().hex[:6]}",
                    description=item.description,
                    status="PENDING",
                    evidence_slot=item.evidence_slot if item.evidence_slot in slots else open_slots[0],
                )
            )

        if not plan_goals:
            # Fallback phased multi-goal plan
            if query_type == "TRACE_FLOW":
                plan_goals = [
                    PlanGoal(
                        id=f"goal_{uuid.uuid4().hex[:6]}",
                        description=f"Identify entrypoint and router definitions for: {query[:50]}",
                        status="PENDING",
                        evidence_slot=open_slots[0],
                    ),
                    PlanGoal(
                        id=f"goal_{uuid.uuid4().hex[:6]}",
                        description="Inspect core service handler and business logic execution path",
                        status="PENDING",
                        evidence_slot=open_slots[1] if len(open_slots) > 1 else open_slots[0],
                    ),
                    PlanGoal(
                        id=f"goal_{uuid.uuid4().hex[:6]}",
                        description="Trace data layer operations and response serialization",
                        status="PENDING",
                        evidence_slot=open_slots[-1],
                    ),
                ]
            else:
                plan_goals = [
                    PlanGoal(
                        id=f"goal_{uuid.uuid4().hex[:6]}",
                        description=f"Locate key files and modules for: {query[:50]}",
                        status="PENDING",
                        evidence_slot=open_slots[0],
                    ),
                    PlanGoal(
                        id=f"goal_{uuid.uuid4().hex[:6]}",
                        description="Inspect code definitions, classes, and logic implementation",
                        status="PENDING",
                        evidence_slot=open_slots[-1],
                    ),
                ]

        current_id = plan_goals[0]["id"] if plan_goals else None

        return {
            "plan": plan_goals,
            "plan_version": state.get("plan_version", 0) + 1,
            "current_goal_id": current_id,
            "next_route": "select_action",
        }
    except Exception:
        fallback_goals = [
            PlanGoal(
                id=f"goal_{uuid.uuid4().hex[:6]}",
                description=f"Locate evidence for {slot}",
                status="PENDING",
                evidence_slot=slot,
            )
            for slot in open_slots
        ]
        return {
            "plan": fallback_goals,
            "plan_version": state.get("plan_version", 0) + 1,
            "current_goal_id": fallback_goals[0]["id"] if fallback_goals else None,
            "next_route": "select_action",
        }
