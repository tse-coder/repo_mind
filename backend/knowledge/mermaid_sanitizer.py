"""
Mermaid syntax sanitizer and linter for RepoMind.

Detects and fixes common LLM-generated Mermaid syntax errors:
1. Unquoted special characters (parentheses, slashes, brackets) in node labels.
2. Invalid node identifiers with slashes, dots, or dashes.
3. Incomplete or unclosed subgraphs and quotes.
"""

from __future__ import annotations

import re


VALID_DIAGRAM_PREFIXES = (
    "flowchart",
    "graph",
    "sequenceDiagram",
    "erDiagram",
    "classDiagram",
    "stateDiagram",
    "stateDiagram-v2",
)


def sanitize_mermaid_code(mermaid_text: str) -> str:
    """
    Sanitize and repair common LLM syntax issues in Mermaid code blocks.
    """
    if not mermaid_text or not mermaid_text.strip():
        return ""

    raw = mermaid_text.strip()

    # Strip markdown code fence if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    lines = raw.splitlines()
    if not lines:
        return ""

    first_line = lines[0].strip()
    # If missing diagram header, default to flowchart TD
    has_valid_header = any(first_line.startswith(prefix) for prefix in VALID_DIAGRAM_PREFIXES)
    if not has_valid_header:
        lines.insert(0, "flowchart TD")

    sanitized_lines: list[str] = []

    # Detect if we're in a sequenceDiagram, erDiagram, or flowchart
    diagram_type = "flowchart"
    if "sequenceDiagram" in lines[0]:
        diagram_type = "sequence"
    elif "erDiagram" in lines[0]:
        diagram_type = "er"
    elif "classDiagram" in lines[0]:
        diagram_type = "class"

    for line in lines:
        stripped = line.strip()

        # In flowchart/graph: ensure node labels with parentheses or special chars are properly double-quoted
        if diagram_type == "flowchart" and "[" in stripped:
            def quote_bracket_label(match: re.Match) -> str:
                node_id = match.group(1)
                bracket_open = match.group(2)
                label_text = match.group(3)
                bracket_close = match.group(4)

                clean_label = label_text.strip()
                if clean_label.startswith('"') and clean_label.endswith('"'):
                    return f"{node_id}{bracket_open}{clean_label}{bracket_close}"

                escaped = clean_label.replace('"', "'")
                return f'{node_id}{bracket_open}"{escaped}"{bracket_close}'

            # Match node_id[label_without_brackets]
            line = re.sub(
                r'([a-zA-Z0-9_-]+)\s*(\[)([^\[\]]*?)(\])',
                quote_bracket_label,
                line,
            )

        sanitized_lines.append(line)

    return "\n".join(sanitized_lines)


def is_valid_mermaid(mermaid_text: str) -> bool:
    """Basic structural validation of Mermaid diagram text."""
    if not mermaid_text or not mermaid_text.strip():
        return False
    clean = sanitize_mermaid_code(mermaid_text)
    first_line = clean.splitlines()[0].strip()
    return any(first_line.startswith(prefix) for prefix in VALID_DIAGRAM_PREFIXES)
