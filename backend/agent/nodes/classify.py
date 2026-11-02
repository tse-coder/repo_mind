"""
classify_node — Analyzes the user question, determines category, entities, and evidence slots.
"""

from __future__ import annotations

from typing import List, Literal
from pydantic import BaseModel, Field

from backend.agent.llm import get_llm
from backend.agent.state import InvestigationState


class QueryClassification(BaseModel):
    """Structured interpretation of the user query."""

    query_type: Literal[
        "LOCATE", "TRACE_FLOW", "ARCHITECTURE", "DEPENDENCY", "ERROR_ORIGIN", "MIXED"
    ] = Field(description="The primary category of the investigation question.")
    entities: List[str] = Field(
        default_factory=list,
        description="Key symbols, file names, routes, or modules explicitly or implicitly referenced.",
    )
    needs_clarification: bool = Field(
        default=False,
        description="True ONLY if the query is critically ambiguous and cannot be resolved by searching the code.",
    )
    clarification_question: str = Field(
        default="",
        description="If needs_clarification is True, the concise question to ask the user.",
    )
    evidence_slots: List[str] = Field(
        default_factory=list,
        description="List of specific sub-questions or facts that must be discovered (e.g. ['entrypoint', 'validation_logic', 'database_call']).",
    )


CLASSIFY_PROMPT = """You are an expert software engineer analyzing a user question about a codebase.
Categorize the question, extract referenced symbols/files/modules, and decompose the question into 1 to 4 concrete evidence slots (facts or code locations required to answer).

Question types:
- LOCATE: Finding where a class, function, or configuration is defined.
- TRACE_FLOW: Tracing execution path from entrypoint to termination/storage.
- ARCHITECTURE: High-level overview of modules, layers, or interactions.
- DEPENDENCY: What a module imports, depends on, or impacts.
- ERROR_ORIGIN: Investigating where an error or exception could originate.
- MIXED: Combination of the above.

Only mark needs_clarification=True if the query is fundamentally unanswerable without user disambiguation (e.g. 'how does it work' with no feature named).
"""


def classify_node(state: InvestigationState) -> dict:
    """Classify the user query and populate evidence slots."""
    query = state.get("query", "")
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(QueryClassification)

    try:
        result: QueryClassification = structured_llm.invoke([
            ("system", CLASSIFY_PROMPT),
            ("human", f"User Question: {query}\nRepository Path: {state.get('repo_path')}"),
        ])

        # Map slots to "OPEN" status dict
        slots_dict = {slot: "OPEN" for slot in result.evidence_slots}
        if not slots_dict:
            slots_dict = {"primary_answer": "OPEN"}

        return {
            "query_type": result.query_type,
            "entities": result.entities,
            "needs_clarification": result.needs_clarification,
            "evidence_slots": slots_dict,
            "next_route": "clarify" if result.needs_clarification else "plan",
        }
    except Exception as e:
        # Fallback heuristic if LLM call fails
        return {
            "query_type": "LOCATE",
            "entities": [],
            "needs_clarification": False,
            "evidence_slots": {"primary_answer": "OPEN"},
            "next_route": "plan",
        }
