"""
synthesize_node — Drafts an answer from recorded findings and evidence.

The answer is structured by query type and includes inline citations.
"""

from backend.agent.state import InvestigationState


def synthesize_node(state: InvestigationState) -> dict:
    """Draft an answer from the evidence and findings collected so far.

    Stub: generates a placeholder answer summarizing what was found.
    Phase 4 replaces with LLM synthesis from findings only.
    """
    findings = state.get("findings", [])
    evidence = state.get("evidence_store", [])
    query = state.get("query", "")
    status = state.get("status", "SUFFICIENT")

    if findings:
        claims = "\n".join(f"- {f['claim']}" for f in findings)
        draft = f"## Investigation Results\n\n**Query:** {query}\n\n**Findings:**\n{claims}"
    elif evidence:
        snippets = "\n".join(f"- [{e['tool_source']}] {e['snippet'][:100]}" for e in evidence)
        draft = f"## Investigation Results\n\n**Query:** {query}\n\n**Evidence collected:**\n{snippets}"
    else:
        draft = f"## Investigation Results\n\n**Query:** {query}\n\n*No evidence was collected during this investigation.*"

    if status == "PARTIAL":
        draft += "\n\n> **Note:** This is a partial answer. Some evidence slots could not be resolved."

    return {
        "draft_answer": draft,
    }
