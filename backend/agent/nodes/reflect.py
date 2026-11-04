"""
reflect_node — Self-critique and strategy adjustment using the Reflexion pattern.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from backend.agent.llm import get_llm
from backend.agent.state import InvestigationState, ReflectionEntry
from backend.config import LLM_PROVIDER


class ReflectionDiagnostic(BaseModel):
    trigger: str = Field(default="Tool call failure or empty result.", description="Summary of the failed or unproductive tool event.")
    diagnosis: str = Field(default="The query or path was likely too restrictive or incorrect.", description="Hypothesis explaining why the action was unsuccessful.")
    next_approach: str = Field(default="Explore the directory structure or try an alternative search strategy.", description="A concrete, adjusted strategy to execute next.")

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        for key in ("ReflectionDiagnostic", "diagnostic", "critique"):
            if key in data and isinstance(data[key], dict):
                data = data[key]
                break
        if "trigger" not in data:
            for alias in ("event", "error", "cause", "issue"):
                if alias in data and isinstance(data[alias], str):
                    data["trigger"] = data[alias]
                    break
        if "diagnosis" not in data:
            for alias in ("reason", "hypothesis", "analysis", "explanation"):
                if alias in data and isinstance(data[alias], str):
                    data["diagnosis"] = data[alias]
                    break
        if "next_approach" not in data:
            for alias in ("solution", "alternative", "next_step", "plan", "adjustment"):
                if alias in data and isinstance(data[alias], str):
                    data["next_approach"] = data[alias]
                    break
        return data


REFLECT_PROMPT = """You are RepoMind's diagnostic critique module.
A tool call either returned an error, was denied by policy, or produced zero relevant code matches.
Analyze the failure, identify why it occurred (e.g. wrong file path, too specific query, wrong tool family),
and propose a concrete, actionable alternative (e.g. broaden query, explore directory tree, or switch from text search to symbol search).
Return your critique strictly as a JSON object adhering to the ReflectionDiagnostic schema.
"""


def reflect_node(state: InvestigationState) -> dict:
    """Diagnose the recent failure and plan an alternative approach."""
    tool_history = state.get("tool_history", [])
    last_call = tool_history[-1] if tool_history else None

    if not last_call:
        entry = ReflectionEntry(
            trigger="general_check",
            diagnosis="No tool calls recorded yet.",
            next_approach="Begin with directory exploration.",
        )
        return {"reflections": [entry], "next_route": "select_action"}

    llm = get_llm(temperature=0.0)
    structured_llm = (
        llm.with_structured_output(ReflectionDiagnostic, method="json_mode")
        if LLM_PROVIDER == "groq"
        else llm.with_structured_output(ReflectionDiagnostic)
    )

    context = f"""
Tool: {last_call['tool_slug']}
Arguments: {last_call['arguments']}
Status: {last_call['status']}
Output Preview: {last_call['output_summary'][:300]}
Open Evidence Slots: {state.get('evidence_slots', {})}
"""

    try:
        diag: ReflectionDiagnostic = structured_llm.invoke([
            ("system", REFLECT_PROMPT),
            ("human", context),
        ])

        entry = ReflectionEntry(
            trigger=diag.trigger,
            diagnosis=diag.diagnosis,
            next_approach=diag.next_approach,
        )
    except Exception:
        entry = ReflectionEntry(
            trigger=f"{last_call['tool_slug']} {last_call['status']}",
            diagnosis="Tool call was unproductive or returned empty results.",
            next_approach="Broaden search parameters or inspect directory structure.",
        )

    return {
        "reflections": [entry],
        "next_route": "select_action",
    }
