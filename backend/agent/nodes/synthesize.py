"""
synthesize_node — Compiles collected findings and evidence into a structured draft answer.
"""

from __future__ import annotations

import re

from backend.agent.llm import get_llm
from backend.agent.state import InvestigationState
from backend.knowledge.mermaid_sanitizer import sanitize_mermaid_code

SYNTHESIZE_PROMPT = """You are RepoMind's synthesis engine.
Synthesize a comprehensive, authoritative technical answer to the user's question using ONLY the provided findings and evidence.

Guidelines & Artifact Standards:
1. Ground every claim directly in the recorded findings and evidence with inline citations: `[filepath:line]` or `[evidence_id]`.
2. Format your response based on the question intent:
   - ARCHITECTURE / SYSTEM OVERVIEW:
     Provide a clear architectural breakdown AND include a clean Mermaid flowchart block:
     ```mermaid
     flowchart TD
       subgraph Presentation ["Presentation Layer"]
         ...
       end
       ...
     ```
   - DATA FLOW / REQUEST LIFECYCLE:
     Provide step-by-step numbered flow AND include a clean Mermaid sequenceDiagram block:
     ```mermaid
     sequenceDiagram
       autonumber
       Client->>Router: ...
     ```
   - DATABASE / DATA MODELS / SCHEMA:
     Provide an entity overview table AND include a Mermaid erDiagram block:
     ```mermaid
     erDiagram
       USER ||--o{ ORDER : has
     ```
   - API CONTRACTS / ENDPOINTS:
     Provide an exhaustive Markdown table with columns: `| Method | Path | Handler | Request Schema | Response Schema | File & Line |`.
3. In Mermaid diagrams: always double-quote node labels containing special characters, e.g. Node["file.py:10 (handler)"].
4. Never invent file paths or code that is not present in the evidence.
"""


def _clean_mermaid_in_text(text: str) -> str:
    """Find and sanitize any ```mermaid ... ``` code blocks in synthesized text."""
    pattern = r"```mermaid([\s\S]*?)```"

    def replacer(match: re.Match) -> str:
        raw_mermaid = match.group(1)
        cleaned = sanitize_mermaid_code(raw_mermaid)
        return f"```mermaid\n{cleaned}\n```"

    return re.sub(pattern, replacer, text)


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
        sanitized_content = _clean_mermaid_in_text(content)
        return {"draft_answer": sanitized_content}
    except Exception:
        # Fallback synthesis
        fallback_lines = [f"## Investigation Results\n\n**Query:** {query}\n\n### Findings:"]
        for f in findings:
            fallback_lines.append(f"- {f['claim']}")
        return {"draft_answer": "\n".join(fallback_lines)}
