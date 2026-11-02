"""
reconcile_node — Resolves contradictory findings using the authority hierarchy:
Executed code > Configuration > Tests > Documentation.
"""

from __future__ import annotations

from backend.agent.llm import get_llm
from backend.agent.state import InvestigationState

RECONCILE_PROMPT = """You are RepoMind's contradiction reconciliation specialist.
Two findings or evidence snippets appear to conflict (e.g. documentation contradicts actual source code).
Apply the strict authority order:
1. Ground-truth code at the pinned commit SHA overrides configuration.
2. Configuration overrides tests.
3. Tests override documentation/comments.

Explain which source takes precedence, cite both files, and provide the resolved finding.
"""


def reconcile_node(state: InvestigationState) -> dict:
    """Resolve conflicting findings and record the reconciled claim."""
    findings = state.get("findings", [])
    if len(findings) < 2:
        return {"next_route": "select_action"}

    # Prompt LLM to analyze the findings and reconcile
    llm = get_llm(temperature=0.0)
    context = "\n".join(f"- {f['claim']} (Evidence: {f['evidence_ids']})" for f in findings[-4:])

    try:
        response = llm.invoke([
            ("system", RECONCILE_PROMPT),
            ("human", f"Resolve potential conflicts among these findings:\n{context}"),
        ])
        content = response.content if isinstance(response.content, str) else str(response.content)

        return {
            "limitations": state.get("limitations", []) + [f"Contradiction Reconciled: {content[:200]}"],
            "next_route": "select_action",
        }
    except Exception:
        return {"next_route": "select_action"}
