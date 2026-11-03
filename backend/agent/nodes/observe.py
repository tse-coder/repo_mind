"""
observe_node — Fast, deterministic evidence extraction from structured tool outputs.

Converts tool outputs directly into EvidenceItem and Finding entries without
requiring a blocking LLM call per step, maximizing execution throughput.
"""

from __future__ import annotations

import hashlib
import uuid

from backend.agent.state import EvidenceItem, Finding, InvestigationState


def observe_node(state: InvestigationState) -> dict:
    """Analyze tool output and record verified evidence and findings."""
    tool_call = state.get("current_tool_call")
    if not tool_call:
        return {}

    tool_slug = tool_call.get("tool_slug", "unknown")
    arguments = tool_call.get("arguments", {})
    policy_status = tool_call.get("policy_status", "APPROVED")
    exec_status = tool_call.get("execution_status", "SUCCESS")
    raw_result = tool_call.get("raw_result", {})

    # If policy denied or execution error, nothing to extract
    if policy_status == "DENIED" or exec_status != "SUCCESS":
        return {"current_tool_call": None}

    new_evidence: list[EvidenceItem] = []
    new_findings: list[Finding] = []
    updated_slots = dict(state.get("evidence_slots", {}))
    open_slot_keys = [k for k, v in updated_slots.items() if v == "OPEN"]
    target_slot = open_slot_keys[0] if open_slot_keys else "primary_answer"

    # 1. read_file output
    if tool_slug == "read_file" and raw_result.get("status") == "SUCCESS":
        content = raw_result.get("content", "")
        file_path = raw_result.get("file_path", arguments.get("file_path", ""))
        s_line = raw_result.get("start_line", 1)
        e_line = raw_result.get("end_line", s_line)
        c_hash = raw_result.get("content_hash", hashlib.sha256(content.encode()).hexdigest()[:16])

        ev_id = f"ev_{uuid.uuid4().hex[:8]}"
        new_evidence.append(
            EvidenceItem(
                id=ev_id,
                file_path=file_path,
                start_line=s_line,
                end_line=e_line,
                content_hash=c_hash,
                snippet=content[:350],
                tool_source="read_file",
                is_direct=True,
            )
        )
        new_findings.append(
            Finding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                claim=f"Read {file_path}:{s_line}-{e_line} confirming code structure.",
                evidence_ids=[ev_id],
                confidence="CONFIRMED",
                slot_id=target_slot,
            )
        )
        if target_slot in updated_slots:
            updated_slots[target_slot] = "SUPPORTED"

    # 2. search_code matches
    elif tool_slug == "search_code" and raw_result.get("status") == "SUCCESS":
        matches = raw_result.get("matches", [])
        for m in matches[:3]:
            ev_id = f"ev_{uuid.uuid4().hex[:8]}"
            new_evidence.append(
                EvidenceItem(
                    id=ev_id,
                    file_path=m["file_path"],
                    start_line=m["line_number"],
                    end_line=m["line_number"],
                    content_hash=hashlib.sha256(m["line"].encode()).hexdigest()[:16],
                    snippet=m["line"],
                    tool_source="search_code",
                    is_direct=False,
                )
            )
        if matches:
            top = matches[0]
            new_findings.append(
                Finding(
                    id=f"find_{uuid.uuid4().hex[:8]}",
                    claim=f"Search '{raw_result.get('query')}' matched in {top['file_path']}:{top['line_number']}.",
                    evidence_ids=[new_evidence[0]["id"]],
                    confidence="INFERRED",
                    slot_id=target_slot,
                )
            )
            if target_slot in updated_slots:
                updated_slots[target_slot] = "SUPPORTED"

    # 3. search_symbols / get_symbol
    elif tool_slug in ("search_symbols", "get_symbol") and raw_result.get("status") == "SUCCESS":
        if tool_slug == "get_symbol" and raw_result.get("symbol"):
            sym = raw_result["symbol"]
            ev_id = f"ev_{uuid.uuid4().hex[:8]}"
            new_evidence.append(
                EvidenceItem(
                    id=ev_id,
                    file_path=sym["file_path"],
                    start_line=sym["start_line"],
                    end_line=sym["end_line"],
                    content_hash=hashlib.sha256(sym.get("signature", "").encode()).hexdigest()[:16],
                    snippet=sym.get("definition_source", "")[:350],
                    tool_source="get_symbol",
                    is_direct=True,
                )
            )
            new_findings.append(
                Finding(
                    id=f"find_{uuid.uuid4().hex[:8]}",
                    claim=f"Symbol '{sym['name']}' defined at {sym['file_path']}:{sym['start_line']}.",
                    evidence_ids=[ev_id],
                    confidence="CONFIRMED",
                    slot_id=target_slot,
                )
            )
            if target_slot in updated_slots:
                updated_slots[target_slot] = "SUPPORTED"
        elif tool_slug == "search_symbols":
            symbols = raw_result.get("symbols", [])
            if symbols:
                top_sym = symbols[0]
                ev_id = f"ev_{uuid.uuid4().hex[:8]}"
                new_evidence.append(
                    EvidenceItem(
                        id=ev_id,
                        file_path=top_sym["file_path"],
                        start_line=top_sym["start_line"],
                        end_line=top_sym["end_line"],
                        content_hash=hashlib.sha256(top_sym["name"].encode()).hexdigest()[:16],
                        snippet=top_sym.get("signature", top_sym["name"]),
                        tool_source="search_symbols",
                        is_direct=False,
                    )
                )
                new_findings.append(
                    Finding(
                        id=f"find_{uuid.uuid4().hex[:8]}",
                        claim=f"Located symbol '{top_sym['name']}' in {top_sym['file_path']}.",
                        evidence_ids=[ev_id],
                        confidence="INFERRED",
                        slot_id=target_slot,
                    )
                )
                if target_slot in updated_slots:
                    updated_slots[target_slot] = "SUPPORTED"

    # 4. semantic_search
    elif tool_slug == "semantic_search" and raw_result.get("status") == "SUCCESS":
        results = raw_result.get("results", [])
        if results:
            top_r = results[0]
            ev_id = f"ev_{uuid.uuid4().hex[:8]}"
            new_evidence.append(
                EvidenceItem(
                    id=ev_id,
                    file_path=top_r["file_path"],
                    start_line=top_r["start_line"],
                    end_line=top_r["end_line"],
                    content_hash=hashlib.sha256(top_r["snippet"].encode()).hexdigest()[:16],
                    snippet=top_r["snippet"][:300],
                    tool_source="semantic_search",
                    is_direct=False,
                )
            )
            new_findings.append(
                Finding(
                    id=f"find_{uuid.uuid4().hex[:8]}",
                    claim=f"Semantic match found in {top_r['file_path']}:{top_r['start_line']} (score: {top_r['score']}).",
                    evidence_ids=[ev_id],
                    confidence="INFERRED",
                    slot_id=target_slot,
                )
            )
            if target_slot in updated_slots:
                updated_slots[target_slot] = "SUPPORTED"

    # 5. explore_tree
    elif tool_slug == "explore_tree" and raw_result.get("status") == "SUCCESS":
        entries = raw_result.get("entries", [])
        ev_id = f"ev_{uuid.uuid4().hex[:8]}"
        summary_snippet = f"Explored {len(entries)} directory entries under {arguments.get('subpath', '.')}"
        new_evidence.append(
            EvidenceItem(
                id=ev_id,
                file_path=arguments.get("subpath", "."),
                start_line=1,
                end_line=len(entries),
                content_hash=hashlib.sha256(summary_snippet.encode()).hexdigest()[:16],
                snippet=summary_snippet,
                tool_source="explore_tree",
                is_direct=False,
            )
        )

    return {
        "evidence_store": new_evidence,
        "findings": new_findings,
        "evidence_slots": updated_slots,
        "current_tool_call": None,
    }
