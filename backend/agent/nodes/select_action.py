"""
select_action_node — Chooses the next read-only tool to execute with a 1-sentence rationale.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Literal
from pydantic import BaseModel, Field

from backend.agent.llm import get_llm
from backend.agent.state import InvestigationState


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
        "get_history",
        "finish",
    ] = Field(description="The tool to execute next, or 'finish' if sufficient evidence is already gathered.")
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments strictly adhering to the selected tool schema.",
    )
    rationale: str = Field(description="A concise 1-sentence explanation of why this specific action is being taken.")


SELECT_ACTION_PROMPT = """You are RepoMind's investigation action selector.
Given the user query, open evidence slots, current plan goal, and tool history, select the single best tool call to advance the investigation.

Available Execution Tools:
1. `explore_tree`: subpath (default '.'), depth (1-3), glob_pattern (e.g. '*.py')
2. `read_file`: file_path (required, relative), start_line, end_line (reads ground-truth code lines)
3. `search_code`: query (literal string or regex), is_regex (bool), path_scope
4. `search_symbols`: query (symbol name substring), kind ('class' | 'function' | 'method')
5. `get_symbol`: symbol_name (required), file_path (optional)
6. `find_references`: symbol_name (required) - finds who calls/references this symbol
7. `get_relationships`: file_path (required), direction ('imports' | 'imported_by')
8. `trace_calls`: entry_symbol (required), depth (default 3)
9. `semantic_search`: query (natural language concept), k (default 5)
10. `get_history`: file_path, max_commits (default 5)
11. `finish`: choose this if you have collected sufficient evidence to answer all slots.

Rules:
- Never repeat the exact same tool call with identical arguments.
- Prefer `search_symbols` or `search_code` when names or keywords are known.
- Prefer `semantic_search` when concept is known but exact identifiers are not.
- Prefer `read_file` to verify exact code and lines before asserting conclusions.
- State your rationale in one clear sentence.
"""


def select_action_node(state: InvestigationState) -> dict:
    """Select the next tool call."""
    query = state.get("query", "")
    slots = state.get("evidence_slots", {})
    open_slots = [k for k, v in slots.items() if v == "OPEN"]
    plan = state.get("plan", [])
    history = state.get("tool_history", [])
    recent_history = history[-4:] if history else []
    reflections = state.get("reflections", [])
    step_count = state.get("step_count", 0)

    # Format history summary for the model
    history_summary = [
        f"Step {h['step']}: {h['tool_slug']} with args {h['arguments']} -> {h['status']}"
        for h in recent_history
    ]

    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(ToolDecision)

    context = f"""
Target Repo: {state.get('repo_path')}
User Query: {query}
Open Evidence Slots: {open_slots}
Active Plan: {[g['description'] for g in plan if g['status'] == 'PENDING'][:2]}
Recent Tool Calls: {history_summary}
Recent Reflections/Adjustments: {[r['next_approach'] for r in reflections[-2:]]}
Step: {step_count + 1} of {state.get('max_steps', 25)}
"""

    try:
        decision: ToolDecision = structured_llm.invoke([
            ("system", SELECT_ACTION_PROMPT),
            ("human", context),
        ])

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
    except Exception:
        # Fallback to explore_tree or search_code
        fallback_tool = "search_code" if state.get("entities") else "explore_tree"
        fallback_args = {"query": state["entities"][0]} if state.get("entities") else {"subpath": ".", "depth": 2}
        return {
            "step_count": step_count + 1,
            "current_tool_call": {
                "tool_slug": fallback_tool,
                "arguments": fallback_args,
                "rationale": f"Investigating repository using {fallback_tool}.",
            },
        }
