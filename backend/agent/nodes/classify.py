"""
classify_node — Analyzes the user question, determines category, entities, and evidence slots.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from backend.agent.llm import get_llm
from backend.agent.state import InvestigationState
from backend.config import LLM_PROVIDER


class QueryClassification(BaseModel):
    """Structured interpretation of the user query."""

    query_type: Literal[
        "LOCATE", "TRACE_FLOW", "ARCHITECTURE", "DEPENDENCY", "ERROR_ORIGIN", "MIXED"
    ] = Field(description="The primary category of the investigation question.")
    entities: list[str] = Field(
        default_factory=list,
        description="Key symbols, file names, routes, or modules explicitly or implicitly referenced, normalized to correct spelling.",
    )
    normalized_query: str = Field(
        default="",
        description="The user query with any obvious code or domain typos corrected (e.g. 'caricullum' -> 'curriculum', 'datas' -> 'data/database/models').",
    )
    needs_clarification: bool = Field(
        default=False,
        description="True ONLY if the query is critically ambiguous and cannot be resolved by searching the code.",
    )
    clarification_question: str = Field(
        default="",
        description="If needs_clarification is True, the concise question to ask the user.",
    )
    evidence_slots: list[str] = Field(
        default_factory=list,
        description="List of 2 to 4 specific sub-questions or facts that must be discovered.",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        for key in ("QueryClassification", "classification"):
            if key in data and isinstance(data[key], dict):
                data = data[key]
                break

        # Normalize query_type to uppercase and map common aliases
        q_type = str(data.get("query_type", "LOCATE")).upper().strip()
        valid_types = {"LOCATE", "TRACE_FLOW", "ARCHITECTURE", "DEPENDENCY", "ERROR_ORIGIN", "MIXED"}
        if q_type not in valid_types:
            if "TRACE" in q_type or "FLOW" in q_type:
                q_type = "TRACE_FLOW"
            elif "ARCH" in q_type:
                q_type = "ARCHITECTURE"
            elif "DEP" in q_type or "IMPORT" in q_type:
                q_type = "DEPENDENCY"
            elif "ERR" in q_type or "BUG" in q_type:
                q_type = "ERROR_ORIGIN"
            else:
                q_type = "LOCATE"
        data["query_type"] = q_type

        # Normalize evidence_slots
        if "evidence_slots" not in data:
            for alias in ("slots", "sub_questions", "facts", "evidence"):
                if alias in data and isinstance(data[alias], list):
                    data["evidence_slots"] = data[alias]
                    break

        return data


CLASSIFY_PROMPT = """You are an expert software engineer analyzing a user question about a codebase.
Categorize the question, extract referenced symbols/files/modules, and decompose the question into 2 to 4 concrete evidence slots (facts or code locations required to answer).

Typo and Entity Normalization:
- If the user query contains obvious typos or misspellings of software terms or domain concepts (e.g. 'caricullum' -> 'curriculum', 'datas' -> 'data/models', 'authe' -> 'auth'), correct them in 'normalized_query' and include the corrected technical terms in 'entities'.

Evidence Slots Decomposition Guidelines:
- Decompose the investigation into 2 to 4 concrete sub-questions / evidence slots.
- For LOCATE: define at least ['symbol_or_module_location', 'definition_and_implementation'].
- For TRACE_FLOW: define at least ['entrypoint_or_router', 'handler_or_service_logic', 'downstream_data_or_response'].
- For ARCHITECTURE: define at least ['core_components_and_layers', 'dependencies_and_configuration'].
- For ERROR_ORIGIN: define at least ['error_trigger_site', 'propagation_path', 'root_cause_logic'].
- AVOID creating only a single vague slot like 'primary_answer'. Decomposing into multi-step slots ensures thorough code investigation.

Question types:
- LOCATE: Finding where a class, function, or configuration is defined.
- TRACE_FLOW: Tracing execution path from entrypoint to termination/storage.
- ARCHITECTURE: High-level overview of modules, layers, or interactions.
- DEPENDENCY: What a module imports, depends on, or impacts.
- ERROR_ORIGIN: Investigating where an error or exception could originate.
- MIXED: Combination of the above.

Only mark needs_clarification=True if the query is fundamentally unanswerable without user disambiguation (e.g. 'how does it work' with no feature named).
Return your response strictly as a JSON object adhering to the schema.
"""


def classify_node(state: InvestigationState) -> dict:
    """Classify the user query and populate evidence slots."""
    query = state.get("query", "")
    llm = get_llm(temperature=0.0)
    structured_llm = (
        llm.with_structured_output(QueryClassification, method="json_mode")
        if LLM_PROVIDER == "groq"
        else llm.with_structured_output(QueryClassification)
    )

    chat_history = state.get("chat_history", [])
    history_ctx = ""
    if len(chat_history) > 1:
        past = [
            f"{m['role'].upper()}: {m['content'][:300]}"
            for m in chat_history[:-1][-4:]
        ]
        history_ctx = "Recent Dialogue Context:\n" + "\n".join(past) + "\n\n"

    try:
        result: QueryClassification = structured_llm.invoke([
            ("system", CLASSIFY_PROMPT),
            ("human", f"{history_ctx}User Question: {query}\nRepository Path: {state.get('repo_path')}"),
        ])

        # Map slots to "OPEN" status dict
        slots_dict = {slot: "OPEN" for slot in result.evidence_slots}
        if not slots_dict:
            if result.query_type == "TRACE_FLOW":
                slots_dict = {
                    "entrypoint_or_router": "OPEN",
                    "service_and_business_logic": "OPEN",
                    "data_flow_and_response": "OPEN",
                }
            elif result.query_type == "LOCATE":
                slots_dict = {
                    "module_and_file_location": "OPEN",
                    "implementation_and_signatures": "OPEN",
                }
            else:
                slots_dict = {
                    "core_definitions": "OPEN",
                    "implementation_details": "OPEN",
                }

        return {
            "query_type": result.query_type,
            "entities": result.entities,
            "needs_clarification": result.needs_clarification,
            "evidence_slots": slots_dict,
            "next_route": "clarify" if result.needs_clarification else "plan",
        }
    except Exception:
        # Fallback heuristic if LLM call fails
        return {
            "query_type": "LOCATE",
            "entities": [],
            "needs_clarification": False,
            "evidence_slots": {
                "module_and_file_location": "OPEN",
                "implementation_and_signatures": "OPEN",
            },
            "next_route": "plan",
        }
