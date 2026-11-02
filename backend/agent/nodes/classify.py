"""
classify_node — Categorizes the user query and identifies evidence slots.

In Phase 1 this is a stub that sets a default classification.
Phase 4 replaces it with an LLM call.
"""

from backend.agent.state import InvestigationState


def classify_node(state: InvestigationState) -> dict:
    """Classify the query type and generate required evidence slots."""
    # ── STUB: default to a LOCATE query with a single evidence slot ────────────
    query = state["query"].lower()

    # Simple heuristic classification (replaced by LLM in Phase 4)
    if any(kw in query for kw in ["trace", "flow", "how does", "step by step"]):
        query_type = "TRACE_FLOW"
    elif any(kw in query for kw in ["architecture", "structure", "overview", "design"]):
        query_type = "ARCHITECTURE"
    elif any(kw in query for kw in ["depend", "import", "impact", "affect"]):
        query_type = "DEPENDENCY"
    elif any(kw in query for kw in ["error", "bug", "crash", "exception", "fail"]):
        query_type = "ERROR_ORIGIN"
    elif any(kw in query for kw in ["where", "find", "locate", "definition"]):
        query_type = "LOCATE"
    else:
        query_type = "MIXED"

    # Stub evidence slots
    evidence_slots = {"primary_answer": "OPEN"}

    return {
        "query_type": query_type,
        "entities": [],
        "needs_clarification": False,
        "evidence_slots": evidence_slots,
        "next_route": "plan",
    }
