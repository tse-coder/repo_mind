"""
answer_node — Produces the final delivered response with confidence labels and metadata.
"""

from __future__ import annotations

from backend.agent.state import InvestigationState


def answer_node(state: InvestigationState) -> dict:
    """Format final output with citations, limitations, and confidence rating."""
    draft = state.get("draft_answer", "")
    limitations = state.get("limitations", [])
    status = state.get("status", "SUFFICIENT")
    step_count = state.get("step_count", 0)
    evidence_count = len(state.get("evidence_store", []))
    findings = state.get("findings", [])

    sections = [draft.strip()]

    # Findings confidence breakdown
    if findings:
        conf_lines = ["\n### Finding Confidence Ratings"]
        for f in findings:
            badge = "🟢 CONFIRMED" if f["confidence"] == "CONFIRMED" else "🟡 INFERRED"
            conf_lines.append(f"- **{badge}**: {f['claim']}")
        sections.append("\n".join(conf_lines))

    # Limitations & caveats
    if limitations:
        lim_lines = ["\n### Limitations & Gaps"]
        for lim in limitations:
            lim_lines.append(f"- {lim}")
        sections.append("\n".join(lim_lines))

    # Meta summary
    sections.append(
        f"\n---\n*Investigation completed with status: **{status}** | "
        f"Steps executed: {step_count} | Evidence citations: {evidence_count}*"
    )

    return {
        "final_answer": "\n\n".join(sections),
        "status": status,
    }
