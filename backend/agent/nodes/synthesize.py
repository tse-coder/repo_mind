"""
synthesize_node — Compiles collected findings and evidence into a structured draft answer.
"""

from __future__ import annotations

from backend.agent.llm import get_llm
from backend.agent.state import InvestigationState

SYNTHESIZE_PROMPT = """You are RepoMind's synthesis engine.
Synthesize a comprehensive, authoritative technical answer to the user's question using ONLY the provided findings and evidence.

Guidelines:
1. Ground every claim directly in the recorded findings and evidence.
2. Structure the answer logically based on query type:
   - TRACE_FLOW: Chronological numbered steps from entry to completion.
   - LOCATE: Explicit file locations, class/function signatures, and descriptions.
   - ARCHITECTURE: Component breakdowns and dependencies.
   - DEPENDENCY: Inbound and outbound imports and impact scope.
3. Use inline code citations format: `[filepath:line]` (e.g. `[services/auth_service.py:12]`).
4. Never invent file paths or code that is not present in the evidence.
"""


def synthesize_node(state: InvestigationState) -> dict:
    """Draft an answer from accumulated findings and evidence."""
    query = state.get("query", "")
    query_type = state.get("query_type", "LOCATE")
    findings = state.get("findings", [])
    evidence = state.get("evidence_store", [])
    status = state.get("status", "SUFFICIENT")

    # If no findings or evidence, state that plainly
    if not findings and not evidence:
        draft = f"## Investigation Results\n\n**Query:** {query}\n\n*Unable to locate relevant code or definitions in the repository for this query.*"
        return {"draft_answer": draft}

    # Format findings and evidence for LLM prompt
    findings_text = "\n".join(
        f"- Claim: {f['claim']} (Confidence: {f['confidence']}, Evidences: {f['evidence_ids']})"
        for f in findings
    )
    evidence_text = "\n".join(
        f"- ID: {e['id']} | File: {e['file_path']}:{e['start_line']}-{e['end_line']} | Snippet: {e['snippet'][:150]}"
        for e in evidence
    )

    context = f"""
User Query: {query}
Investigation Type: {query_type}
Investigation Status: {status}

Findings:
{findings_text}

Evidence Citations:
{evidence_text}
"""

    llm = get_llm(temperature=0.0)
    try:
        response = llm.invoke([
            ("system", SYNTHESIZE_PROMPT),
            ("human", context),
        ])
        content = response.content if isinstance(response.content, str) else str(response.content)
        return {"draft_answer": content}
    except Exception as e:
        # Fallback synthesis
        fallback_lines = [f"## Investigation Results\n\n**Query:** {query}\n\n### Findings:"]
        for f in findings:
            fallback_lines.append(f"- {f['claim']}")
        return {"draft_answer": "\n".join(fallback_lines)}
