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
            # If reading a doc file for a code/logic slot, treat as INFERRED rather than terminating
            is_doc = file_path.endswith((".md", ".rst", ".txt"))
            slot_is_doc = "doc" in target_slot.lower() or "read" in target_slot.lower()
            updated_slots[target_slot] = "SUPPORTED" if (not is_doc or slot_is_doc) else "INFERRED"

    # 2. search_code matches
    elif tool_slug == "search_code" and raw_result.get("status") == "SUCCESS":
        matches = raw_result.get("matches", [])
        for m in matches[:20]:
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
                    claim=f"Search '{raw_result.get('query')}' matched {len(matches)} lines across {len(set(m['file_path'] for m in matches))} files (e.g. {top['file_path']}:{top['line_number']}).",
                    evidence_ids=[new_evidence[0]["id"]],
                    confidence="INFERRED",
                    slot_id=target_slot,
                )
            )
            if target_slot in updated_slots:
                updated_slots[target_slot] = "INFERRED"

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
            for sym in symbols[:25]:
                ev_id = f"ev_{uuid.uuid4().hex[:8]}"
                new_evidence.append(
                    EvidenceItem(
                        id=ev_id,
                        file_path=sym["file_path"],
                        start_line=sym["start_line"],
                        end_line=sym["end_line"],
                        content_hash=hashlib.sha256(sym["name"].encode()).hexdigest()[:16],
                        snippet=f"{sym.get('kind', 'symbol')} {sym['name']}{sym.get('signature', '')}",
                        tool_source="search_symbols",
                        is_direct=False,
                    )
                )
            if symbols:
                new_findings.append(
                    Finding(
                        id=f"find_{uuid.uuid4().hex[:8]}",
                        claim=f"Symbol search for '{raw_result.get('query')}' found {len(symbols)} symbols: {', '.join(s['name'] for s in symbols[:12])}.",
                        evidence_ids=[e["id"] for e in new_evidence],
                        confidence="INFERRED",
                        slot_id=target_slot,
                    )
                )
                if target_slot in updated_slots:
                    updated_slots[target_slot] = "INFERRED"

    # 4. semantic_search / search_docs
    elif tool_slug in ("semantic_search", "search_docs") and raw_result.get("status") == "SUCCESS":
        results = raw_result.get("results", [])
        for top_r in results[:5]:
            ev_id = f"ev_{uuid.uuid4().hex[:8]}"
            new_evidence.append(
                EvidenceItem(
                    id=ev_id,
                    file_path=top_r["file_path"],
                    start_line=top_r["start_line"],
                    end_line=top_r["end_line"],
                    content_hash=hashlib.sha256(top_r["snippet"].encode()).hexdigest()[:16],
                    snippet=top_r["snippet"][:300],
                    tool_source=tool_slug,
                    is_direct=False,
                )
            )
        if results:
            top_r = results[0]
            heading = top_r.get("heading") or ""
            heading_bit = f" ({heading})" if heading else ""
            new_findings.append(
                Finding(
                    id=f"find_{uuid.uuid4().hex[:8]}",
                    claim=f"Semantic match found in {top_r['file_path']}:{top_r['start_line']}{heading_bit} (score: {top_r['score']}).",
                    evidence_ids=[ev_id],
                    confidence="INFERRED",
                    slot_id=target_slot,
                )
            )
            if target_slot in updated_slots:
                updated_slots[target_slot] = "INFERRED"

    # 5. explore_tree
    elif tool_slug == "explore_tree" and raw_result.get("status") == "SUCCESS":
        entries = raw_result.get("entries", [])
        files = [e["path"] for e in entries if e.get("type") == "file"]
        dirs = [e["path"] for e in entries if e.get("type") == "directory"]
        subpath = arguments.get("subpath", ".")

        # Create valid evidence for top discovered code files, or directory if empty
        if files:
            for fpath in files[:3]:
                ev_id = f"ev_{uuid.uuid4().hex[:8]}"
                new_evidence.append(
                    EvidenceItem(
                        id=ev_id,
                        file_path=fpath,
                        start_line=1,
                        end_line=1,
                        content_hash=hashlib.sha256(fpath.encode()).hexdigest()[:16],
                        snippet=f"Discovered file under {subpath}: {fpath}",
                        tool_source="explore_tree",
                        is_direct=False,
                    )
                )
        else:
            ev_id = f"ev_{uuid.uuid4().hex[:8]}"
            new_evidence.append(
                EvidenceItem(
                    id=ev_id,
                    file_path=subpath,
                    start_line=1,
                    end_line=1,
                    content_hash=hashlib.sha256(f"empty:{subpath}".encode()).hexdigest()[:16],
                    snippet=f"Explored directory '{subpath}': no files found ({len(dirs)} subdirectories).",
                    tool_source="explore_tree",
                    is_direct=False,
                )
            )

        new_findings.append(
            Finding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                claim=f"Directory '{subpath}' contains {len(entries)} entries ({len(files)} files, {len(dirs)} dirs). Discovered files: {', '.join(files[:12])}.",
                evidence_ids=[e["id"] for e in new_evidence],
                confidence="CONFIRMED",
                slot_id=target_slot,
            )
        )
        if target_slot in updated_slots:
            updated_slots[target_slot] = "INFERRED"

    # 6. get_history
    elif tool_slug == "get_history" and raw_result.get("status") == "SUCCESS":
        commits = raw_result.get("commits", [])
        fpath = arguments.get("file_path") or "repo"
        if commits:
            top_commits = commits[:5]
            summary_lines = [f"{c['sha'][:8]} ({c['date']}): {c['message']} [{c['author']}]" for c in top_commits]
            snippet = "\n".join(summary_lines)
            ev_id = f"ev_{uuid.uuid4().hex[:8]}"
            new_evidence.append(
                EvidenceItem(
                    id=ev_id,
                    file_path=fpath if fpath != "repo" else "git:HEAD",
                    start_line=1,
                    end_line=len(top_commits),
                    content_hash=hashlib.sha256(snippet.encode()).hexdigest()[:16],
                    snippet=snippet,
                    tool_source="get_history",
                    is_direct=True,
                )
            )
            new_findings.append(
                Finding(
                    id=f"find_{uuid.uuid4().hex[:8]}",
                    claim=f"Retrieved {len(commits)} commits for '{fpath}'. Latest: '{commits[0]['message']}' by {commits[0]['author']} on {commits[0]['date']}.",
                    evidence_ids=[ev_id],
                    confidence="CONFIRMED",
                    slot_id=target_slot,
                )
            )
            if target_slot in updated_slots:
                updated_slots[target_slot] = "SUPPORTED"

    # 7. find_references
    elif tool_slug == "find_references" and raw_result.get("status") == "SUCCESS":
        refs = raw_result.get("references", [])
        sym = raw_result.get("symbol_name", "")
        for r in refs[:3]:
            ev_id = f"ev_{uuid.uuid4().hex[:8]}"
            new_evidence.append(
                EvidenceItem(
                    id=ev_id,
                    file_path=r["file_path"],
                    start_line=r["line_number"],
                    end_line=r["line_number"],
                    content_hash=hashlib.sha256(f"{r['caller_name']}->{sym}".encode()).hexdigest()[:16],
                    snippet=f"Caller '{r['caller_name']}' references symbol '{sym}'",
                    tool_source="find_references",
                    is_direct=False,
                )
            )
        if refs:
            top_ref = refs[0]
            new_findings.append(
                Finding(
                    id=f"find_{uuid.uuid4().hex[:8]}",
                    claim=f"Symbol '{sym}' is referenced in {len(refs)} locations (e.g. {top_ref['file_path']}:{top_ref['line_number']} by '{top_ref['caller_name']}').",
                    evidence_ids=[e["id"] for e in new_evidence],
                    confidence="CONFIRMED",
                    slot_id=target_slot,
                )
            )
            if target_slot in updated_slots:
                updated_slots[target_slot] = "SUPPORTED"

    # 8. get_relationships
    elif tool_slug == "get_relationships" and raw_result.get("status") == "SUCCESS":
        rels = raw_result.get("relationships", [])
        fpath = raw_result.get("file_path", "")
        direction = raw_result.get("direction", "imports")
        if rels:
            dep_names = [r.get("module", "") for r in rels[:8]]
            snippet = f"{direction}: {', '.join(dep_names)}"
            ev_id = f"ev_{uuid.uuid4().hex[:8]}"
            new_evidence.append(
                EvidenceItem(
                    id=ev_id,
                    file_path=fpath,
                    start_line=1,
                    end_line=len(rels),
                    content_hash=hashlib.sha256(snippet.encode()).hexdigest()[:16],
                    snippet=snippet,
                    tool_source="get_relationships",
                    is_direct=True,
                )
            )
            new_findings.append(
                Finding(
                    id=f"find_{uuid.uuid4().hex[:8]}",
                    claim=f"File '{fpath}' has {len(rels)} {direction} dependencies: {', '.join(dep_names[:6])}.",
                    evidence_ids=[ev_id],
                    confidence="CONFIRMED",
                    slot_id=target_slot,
                )
            )
            if target_slot in updated_slots:
                updated_slots[target_slot] = "SUPPORTED"

    # 9. trace_calls
    elif tool_slug == "trace_calls" and raw_result.get("status") == "SUCCESS":
        call_tree = raw_result.get("call_tree", {})
        entry_sym = raw_result.get("entry_symbol", "")
        calls = call_tree.get("calls", []) if isinstance(call_tree, dict) else []
        callee_names = [c.get("symbol", "") for c in calls if isinstance(c, dict)]
        snippet = f"Entry: {entry_sym} calls -> {', '.join(callee_names)}"
        ev_id = f"ev_{uuid.uuid4().hex[:8]}"
        new_evidence.append(
            EvidenceItem(
                id=ev_id,
                file_path=call_tree.get("file_path", "ast_call_tree"),
                start_line=1,
                end_line=len(calls) or 1,
                content_hash=hashlib.sha256(snippet.encode()).hexdigest()[:16],
                snippet=snippet,
                tool_source="trace_calls",
                is_direct=False,
            )
        )
        new_findings.append(
            Finding(
                id=f"find_{uuid.uuid4().hex[:8]}",
                claim=f"Call trace from entry '{entry_sym}' reaches {len(callee_names)} direct callees: {', '.join(callee_names[:6])}.",
                evidence_ids=[ev_id],
                confidence="CONFIRMED",
                slot_id=target_slot,
            )
        )
        if target_slot in updated_slots:
            updated_slots[target_slot] = "SUPPORTED"

    return {
        "evidence_store": new_evidence,
        "findings": new_findings,
        "evidence_slots": updated_slots,
        "current_tool_call": None,
    }
