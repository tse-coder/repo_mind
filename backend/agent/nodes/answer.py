"""
answer_node — Produces the final formatted answer with citations and confidence labels.
"""

from backend.agent.state import InvestigationState


def answer_node(state: InvestigationState) -> dict:
    """Finalize the answer with confidence labels and limitations.

    Takes the (optionally verified) draft and appends metadata:
    - Confidence labels per finding
    - Limitations section
    - Investigation summary
    """
    draft = state.get("draft_answer", "")
    limitations = state.get("limitations", [])
    status = state.get("status", "SUFFICIENT")
    step_count = state.get("step_count", 0)
    evidence_count = len(state.get("evidence_store", []))
    finding_count = len(state.get("findings", []))

    # Build the final answer
    sections = [draft]

    # Limitations
    if limitations:
        lim_text = "\n".join(f"- {lim}" for lim in limitations)
        sections.append(f"\n### Limitations\n{lim_text}")

    # Investigation metadata
    sections.append(
        f"\n---\n*Investigation completed with status: **{status}** "
        f"| Steps: {step_count} | Evidence items: {evidence_count} "
        f"| Findings: {finding_count}*"
    )

    final_answer = "\n".join(sections)

    return {
        "final_answer": final_answer,
        "status": status if status in ("SUFFICIENT", "PARTIAL") else "SUFFICIENT",
    }
