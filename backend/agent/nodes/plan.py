"""
plan_node — Creates or revises the investigation plan.

Generates a versioned list of sub-goals mapped to open evidence slots.
"""

import uuid

from backend.agent.state import InvestigationState, PlanGoal


def plan_node(state: InvestigationState) -> dict:
    """Create or revise the investigation plan based on current evidence slots.

    Stub: creates a single goal per open evidence slot.
    Phase 4 replaces this with LLM-driven planning.
    """
    open_slots = [
        slot for slot, status in state["evidence_slots"].items() if status == "OPEN"
    ]

    plan: list[PlanGoal] = []
    for slot_name in open_slots:
        plan.append(
            PlanGoal(
                id=f"goal_{uuid.uuid4().hex[:6]}",
                description=f"Investigate: {slot_name}",
                status="PENDING",
                evidence_slot=slot_name,
            )
        )

    # Set the first pending goal as current
    current_goal_id = plan[0]["id"] if plan else None

    return {
        "plan": plan,
        "plan_version": state["plan_version"] + 1,
        "current_goal_id": current_goal_id,
        "next_route": "select_action",
    }
