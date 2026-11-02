"""
Untrusted repository content framing and secret redaction wrapper.

Wraps raw file and tool outputs with explicit boundary delimiters:
<<<UNTRUSTED_REPOSITORY_DATA ...>>> ... <<<END_UNTRUSTED_REPOSITORY_DATA>>>
Ensures that prompt injection attempts inside repo text are treated strictly as data.
"""

from __future__ import annotations

import json
from typing import Any

from backend.knowledge.secret_scanner import redact_secrets


def frame_untrusted_content(
    source_tool: str,
    raw_output: Any,
    file_path: str = "",
    line_range: str = "",
    max_chars: int = 4000,
) -> str:
    """Format and frame output as untrusted external repository data with secret redaction."""
    # Convert output to string representation
    if isinstance(raw_output, (dict, list)):
        text_body = json.dumps(raw_output, indent=2, ensure_ascii=False)
    else:
        text_body = str(raw_output)

    # 1. Redact secrets
    redacted_body = redact_secrets(text_body)

    # 2. Output size truncation if needed
    is_truncated = False
    if len(redacted_body) > max_chars:
        redacted_body = redacted_body[:max_chars] + "\n... [TRUNCATED DUE TO SIZE LIMIT] ..."
        is_truncated = True

    meta_attrs = [f'source="{source_tool}"']
    if file_path:
        meta_attrs.append(f'file="{file_path}"')
    if line_range:
        meta_attrs.append(f'lines="{line_range}"')
    if is_truncated:
        meta_attrs.append('truncated="true"')

    header = f"<<<UNTRUSTED_REPOSITORY_DATA: {' '.join(meta_attrs)}>>>"
    footer = "<<<END_UNTRUSTED_REPOSITORY_DATA>>>"

    return f"{header}\n{redacted_body}\n{footer}"
