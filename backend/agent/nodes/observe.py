"""
observe_node — Processes tool output and extracts evidence items.

Wraps raw output in untrusted content frames and converts
useful observations into EvidenceItem entries.
"""

import hashlib
import uuid

from backend.agent.state import EvidenceItem, InvestigationState


def observe_node(state: InvestigationState) -> dict:
    """Process tool output and extract evidence.

    Stub: creates a synthetic evidence item from the stub tool output.
    Phase 4 replaces this with LLM-driven evidence assessment.
    """
    tool_call = state.get("current_tool_call")
    if tool_call is None:
        return {}

    tool_slug = tool_call.get("tool_slug", "unknown")
    output = tool_call.get("output", "")
    exec_status = tool_call.get("execution_status", "SUCCESS")

    # If the tool was denied or failed, no evidence to extract
    if tool_call.get("policy_status") == "DENIED" or exec_status != "SUCCESS":
        return {"current_tool_call": None}

    # Stub: create a placeholder evidence item
    evidence = EvidenceItem(
        id=f"ev_{uuid.uuid4().hex[:8]}",
        file_path="(stub)",
        start_line=0,
        end_line=0,
        content_hash=hashlib.sha256(output.encode()).hexdigest()[:16],
        snippet=output[:200],
        tool_source=tool_slug,
        is_direct=False,
    )

    return {
        "evidence_store": [evidence],
        "current_tool_call": None,
    }
