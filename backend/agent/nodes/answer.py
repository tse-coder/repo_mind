"""
answer_node — Produces the final delivered response with confidence labels and metadata.
"""

from __future__ import annotations

from backend.agent.state import InvestigationState


def answer_node(state: InvestigationState) -> dict:
    """Format final output with citations and limitations."""
    draft = state.get("draft_answer", "")
    limitations = state.get("limitations", [])
    raw_status = state.get("status", "SUFFICIENT")
    if raw_status in ("RUNNING", "INITIALIZED"):
        status = "PARTIAL" if limitations else "SUFFICIENT"
    else:
        status = raw_status

    sections = [draft.strip()]

    # Limitations & caveats
    if limitations:
        lim_lines = ["\n### Limitations & Gaps"]
        for lim in limitations:
            lim_lines.append(f"- {lim}")
        sections.append("\n".join(lim_lines))

    final_text = "\n\n".join(sections)
    return {
        "final_answer": final_text,
        "status": status,
        "chat_history": [{"role": "assistant", "content": final_text}],
    }
