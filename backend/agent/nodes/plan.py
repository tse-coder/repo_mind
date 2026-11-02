"""
plan_node — Creates or revises an investigation plan based on open evidence slots.
"""

from __future__ import annotations

import uuid
from typing import List
from pydantic import BaseModel, Field

from backend.agent.llm import get_llm
from backend.agent.state import InvestigationState, PlanGoal


class PlannedGoalItem(BaseModel):
    description: str = Field(description="Actionable goal statement for this investigation step.")
    evidence_slot: str = Field(description="The evidence slot this goal will help satisfy.")


class PlanProposal(BaseModel):
    goals: List[PlannedGoalItem] = Field(description="Ordered list of investigation sub-goals.")
    revision_reason: str = Field(default="", description="If revising an existing plan, explanation of why.")


PLAN_PROMPT = """You are a software investigation planner.
Based on the user's question, query type, and open evidence slots, generate a concise, ordered list of 1 to 4 investigation goals.
Each goal should be tied to an open evidence slot.
Focus on finding concrete code definitions, usages, or flow steps using read-only tools.
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

    # Single open slot shortcut
    if len(open_slots) == 1 and not existing_plan:
        goal = PlanGoal(
            id=f"goal_{uuid.uuid4().hex[:6]}",
            description=f"Investigate: {open_slots[0]}",
            status="PENDING",
            evidence_slot=open_slots[0],
        )
        return {
            "plan": [goal],
            "plan_version": state.get("plan_version", 0) + 1,
            "current_goal_id": goal["id"],
            "next_route": "select_action",
        }

    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(PlanProposal)

    prompt_context = f"""
Query: {query}
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
            plan_goals = [
                PlanGoal(
                    id=f"goal_{uuid.uuid4().hex[:6]}",
                    description=f"Resolve {open_slots[0]}",
                    status="PENDING",
                    evidence_slot=open_slots[0],
                )
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
