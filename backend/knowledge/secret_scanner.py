"""
Secret detection and redaction scanner for RepoMind.

Scans content for common API keys, private keys, and high-entropy secrets
to prevent sensitive data leakage into LLM prompts or UI views.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretMatch:
    pattern_name: str
    line_number: int
    matched_text: str


SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "AWS_ACCESS_KEY": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "AWS_SECRET_KEY": re.compile(r"(?i)aws_secret_access_key\s*=\s*(?:\\\\*['\"])?[A-Za-z0-9/+=]{40}(?:\\\\*['\"])?"),
    "GENERIC_API_KEY": re.compile(r"(?i)(?:api_key|apikey|secret_key|auth_token)\s*[:=]\s*(?:\\\\*['\"])?[A-Za-z0-9_\-]{20,}(?:\\\\*['\"])?"),
    "GITHUB_TOKEN": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}\b"),
    "PRIVATE_KEY": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "JWT_TOKEN": re.compile(r"\beyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b"),
}


def scan_for_secrets(content: str) -> list[SecretMatch]:
    """Scan multiline text for potential secrets."""
    matches: list[SecretMatch] = []
    lines = content.splitlines()

    for line_idx, line in enumerate(lines, start=1):
        for name, pattern in SECRET_PATTERNS.items():
            for m in pattern.finditer(line):
                matches.append(
                    SecretMatch(
                        pattern_name=name,
                        line_number=line_idx,
                        matched_text=m.group(0),
                    )
                )

    return matches


def redact_secrets(content: str) -> str:
    """Replace all detected secrets in content with safe redaction notices."""
    redacted = content
    for name, pattern in SECRET_PATTERNS.items():
        redacted = pattern.sub(f"[REDACTED_{name}]", redacted)
    return redacted
