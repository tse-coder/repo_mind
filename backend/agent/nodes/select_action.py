"""
select_action_node — Chooses the next read-only tool to execute with a 1-sentence rationale.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from backend.agent.llm import get_llm
from backend.agent.state import InvestigationState
from backend.config import LLM_PROVIDER

logger = logging.getLogger("repomind.action")


class ToolDecision(BaseModel):
    tool_slug: Literal[
        "explore_tree",
        "read_file",
        "search_code",
        "search_symbols",
        "get_symbol",
        "find_references",
        "get_relationships",
        "trace_calls",
        "semantic_search",
        "search_docs",
        "get_history",
        "finish",
    ] = Field(
        default="explore_tree",
        description="The tool to execute next, or 'finish' if sufficient evidence is already gathered.",
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments strictly adhering to the selected tool schema.",
    )
    rationale: str = Field(
        default="Investigating repository to gather factual evidence.",
        description="A concise 1-sentence explanation of why this specific action is being taken.",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Check for nested envelopes like {"ToolDecision": {...}} or {"tool": {...}}
        for key in ("ToolDecision", "tool_decision", "action", "decision"):
            if key in data and isinstance(data[key], dict):
                data = data[key]
                break

        # Map function / name / tool to tool_slug
        if "tool_slug" not in data:
            for alias in ("function", "name", "tool", "tool_name", "action", "selected_tool"):
                if alias in data and isinstance(data[alias], str):
                    data["tool_slug"] = data[alias]
                    break

        # Normalize arguments
        if "arguments" not in data:
            for alias in ("args", "parameters", "params", "input"):
                if alias in data and isinstance(data[alias], dict):
                    data["arguments"] = data[alias]
                    break

        # Normalize rationale
        if "rationale" not in data or not data["rationale"]:
            for alias in ("reason", "thought", "explanation", "justification"):
                if alias in data and isinstance(data[alias], str):
                    data["rationale"] = data[alias]
                    break
            if "rationale" not in data or not data["rationale"]:
                data["rationale"] = f"Executing {data.get('tool_slug', 'tool')} to advance investigation."

        return data


SELECT_ACTION_PROMPT = """You are RepoMind's investigation action selector.
Given the user query, open evidence slots, current plan goal, and tool history, select the single best tool call to advance the investigation.
Output your decision strictly as a JSON object matching the ToolDecision schema: {"tool_slug": "...", "arguments": {...}, "rationale": "..."}.

Available Execution Tools:
1. `explore_tree`: subpath (default '.'), depth (1-3), glob_pattern (e.g. '*.py', '*.cpp', '*.h')
2. `read_file`: file_path (required, relative), start_line, end_line (reads ground-truth code lines)
3. `search_code`: query (literal string or regex), is_regex (bool), path_scope
4. `search_symbols`: query (symbol name substring), kind ('class' | 'function' | 'method')
5. `get_symbol`: symbol_name (required), file_path (optional)
6. `find_references`: symbol_name (required) - finds who calls/references this symbol
7. `get_relationships`: file_path (required), direction ('imports' | 'imported_by')
8. `trace_calls`: entry_symbol (required), depth (default 3)
9. `semantic_search`: query (natural language concept over source code), k (default 5)
10. `search_docs`: query (why/design/architecture/policy questions), k (default 5) — heading-aware RAG over README, docs/, ADR/, RFC
11. `get_history`: file_path, max_commits (default 5)
12. `finish`: choose this if you have collected sufficient evidence and verified ground-truth line citations.

Investigation Guidelines & Strict Rules:
- USER DIRECTIVE PRIORITY: If the user's latest query explicitly mentions a tool, action, or resource (e.g. 'explore git histories' -> `get_history`, 'check docs' -> `search_docs` or `read_file('README.md')`, 'trace calls' -> `trace_calls`), you MUST prioritize that specific tool on your next step!
- NEVER repeat the exact same tool call with identical arguments as a previous step.
- DO NOT search for the repository name itself. Search for technical concepts, identifiers, function names, classes, or keywords from the user question.
- TRACE_FLOW FOLLOW-THROUGH: When tracing execution paths or data flow, if a previous step identified a router, handler, or module import (e.g. `main.py` including `curriculum_router` from `app/api/curriculum.py`), your NEXT action MUST be to inspect that router or service file with `read_file`! Do not stop at the entrypoint.
- TYPO RESILIENCE & SEARCH FALLBACK: If a literal `search_code` returned 0 matches, DO NOT try the exact same query again. Immediately switch to `semantic_search` or use `explore_tree` on subdirectories (`subpath='app'`, `subpath='src'`) to find where the feature lives.
- GROUND TRUTH CITATIONS: Once key source files are identified from `explore_tree` or code searches, IMMEDIATELY call `read_file` to inspect the code and collect verifiable line citations. Line citations ONLY come from reading files.
- INVENTORY / REPO-WIDE LISTS: When asked to list, inventory, or categorize all functions, classes, or endpoints across the repo, use search_symbols with query='' or query='*' and kind='function' to retrieve symbols in bulk, then inspect key modules with read_file.
- State your rationale in one clear sentence.
"""


def select_action_node(state: InvestigationState) -> dict:
    """Select the next tool call."""
    query = state.get("query", "")
    slots = state.get("evidence_slots", {})
    open_slots = [k for k, v in slots.items() if v == "OPEN"]
    plan = state.get("plan", [])
    history = state.get("tool_history", [])
    recent_history = history[-5:] if history else []
    reflections = state.get("reflections", [])
    step_count = state.get("step_count", 0)

    # Format history summary with tool output summary
    history_summary = []
    for h in recent_history:
        summary_snip = h.get("output_summary", "")
        summary_snip = summary_snip.replace("<<<UNTRUSTED_REPOSITORY_DATA>>>", "").replace("<<<END_UNTRUSTED_REPOSITORY_DATA>>>", "").strip()
        if len(summary_snip) > 280:
            summary_snip = summary_snip[:280] + "..."
        history_summary.append(
            f"Step {h['step']}: {h['tool_slug']}({h['arguments']}) -> {h['status']}\n  Result: {summary_snip}"
        )

    findings = state.get("findings", [])
    findings_summary = [f"- {f['claim']}" for f in findings[-4:]] if findings else ["No findings recorded yet."]

    evidence = state.get("evidence_store", [])
    inspected_files = list({e["file_path"] for e in evidence if e.get("file_path")})

    llm = get_llm(temperature=0.0)
    structured_llm = (
        llm.with_structured_output(ToolDecision, method="json_mode")
        if LLM_PROVIDER == "groq"
        else llm.with_structured_output(ToolDecision)
    )

    chat_history = state.get("chat_history", [])
    history_ctx = ""
    if len(chat_history) > 1:
        past = [
            f"{m['role'].upper()}: {m['content'][:200]}"
            for m in chat_history[:-1][-3:]
        ]
        history_ctx = "Prior Conversation:\n" + "\n".join(past) + "\n"

    context = f"""Target Repo: {state.get('repo_path')}
{history_ctx}User Query: {query}
Open Evidence Slots: {open_slots}
Active Plan Goals: {[g['description'] for g in plan if g['status'] == 'PENDING'][:2]}
Verified Files Already Read: {inspected_files}
Current Findings:
{chr(10).join(findings_summary)}
Recent Tool Calls & Results:
{chr(10).join(history_summary) if history_summary else 'No tool calls yet.'}
Recent Reflections/Adjustments: {[r['next_approach'] for r in reflections[-2:]]}
Step: {step_count + 1} of {state.get('max_steps', 20)}
"""

    try:
        decision: ToolDecision = structured_llm.invoke([
            ("system", SELECT_ACTION_PROMPT),
            ("human", context),
        ])

        # Anti-loop check: prevent calling identical tool + arguments as previous step
        if recent_history and decision.tool_slug != "finish":
            last = recent_history[-1]
            if decision.tool_slug == last.get("tool_slug") and decision.arguments == last.get("arguments"):
                logger.warning(
                    "Duplicate tool call detected (%s, args=%s). Forcing alternative.",
                    decision.tool_slug,
                    decision.arguments,
                )
                if decision.tool_slug == "explore_tree":
                    # If explore_tree was repeated, inspect README or source directory
                    decision = ToolDecision(
                        tool_slug="read_file",
                        arguments={"file_path": "README.md", "start_line": 1, "end_line": 80},
                        rationale="Reading README.md to understand project layout and entry points.",
                    )
                elif decision.tool_slug == "search_code":
                    decision = ToolDecision(
                        tool_slug="semantic_search",
                        arguments={"query": query, "k": 3},
                        rationale="Switching to semantic concept search since literal search was repeated.",
                    )

        if decision.tool_slug == "finish":
            return {
                "step_count": step_count + 1,
                "current_tool_call": None,
                "next_route": "synthesize",
            }

        return {
            "step_count": step_count + 1,
            "current_tool_call": {
                "tool_slug": decision.tool_slug,
                "arguments": decision.arguments,
                "rationale": decision.rationale,
            },
        }
    except Exception as e:
        logger.error("Action selection LLM invocation failed: %s", e, exc_info=True)
        # Smart adaptive fallback avoiding repetition
        used_tools = {h["tool_slug"] for h in recent_history}
        if "explore_tree" not in used_tools:
            fallback_tool = "explore_tree"
            fallback_args = {"subpath": ".", "depth": 2}
        elif "read_file" not in used_tools:
            fallback_tool = "read_file"
            fallback_args = {"file_path": "README.md", "start_line": 1, "end_line": 60}
        else:
            fallback_tool = "semantic_search"
            fallback_args = {"query": query, "k": 3}

        return {
            "step_count": step_count + 1,
            "current_tool_call": {
                "tool_slug": fallback_tool,
                "arguments": fallback_args,
                "rationale": f"Investigating repository using {fallback_tool}.",
            },
        }
