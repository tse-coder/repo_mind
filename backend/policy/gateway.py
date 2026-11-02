"""
Policy Gateway for RepoMind.

Enforces mechanical safety rules before any tool executes:
1. Path confinement (blocks path traversals ../../ outside the target repository).
2. Tool allowlist enforcement.
3. Budget and step limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class PolicyCheckResult:
    allowed: bool
    status: str  # "APPROVED" | "DENIED"
    reason: Optional[str] = None
    sanitized_args: Optional[dict[str, Any]] = None


# Allowed execution and meta tools
ALLOWED_TOOL_SLUGS = frozenset({
    # Execution tools
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
    # Meta tools
    "update_plan",
    "record_finding",
    "reflect_on_findings",
    "request_clarification",
    "finish",
})

# Path argument parameter names to check for path traversal
PATH_ARG_NAMES = ("file_path", "subpath", "path_scope", "target_path")


class PolicyGateway:
    """Validates and enforces security constraints on all tool invocations."""

    def __init__(self, repo_path: str):
        self.repo_root = Path(repo_path).resolve()

    def validate(
        self,
        tool_slug: str,
        arguments: dict[str, Any],
        step_count: int,
        max_steps: int,
    ) -> PolicyCheckResult:
        """Validate a proposed tool call."""
        # 1. Tool allowlist check
        if tool_slug not in ALLOWED_TOOL_SLUGS:
            return PolicyCheckResult(
                allowed=False,
                status="DENIED",
                reason=f"Tool '{tool_slug}' is not on the permitted tools allowlist.",
            )

        # 2. Step budget check
        if step_count >= max_steps:
            return PolicyCheckResult(
                allowed=False,
                status="DENIED",
                reason=f"Step budget reached ({step_count}/{max_steps}). Further tool calls blocked.",
            )

        # 3. Path confinement check
        for param in PATH_ARG_NAMES:
            if param in arguments and arguments[param] is not None:
                val = str(arguments[param]).strip()
                # If an absolute path is passed, or if relative traversal escapes repo_root
                try:
                    resolved = (self.repo_root / val).resolve()
                    if not resolved.is_relative_to(self.repo_root):
                        return PolicyCheckResult(
                            allowed=False,
                            status="DENIED",
                            reason=f"Security violation: path '{val}' escapes the repository root.",
                        )
                except (ValueError, RuntimeError) as e:
                    return PolicyCheckResult(
                        allowed=False,
                        status="DENIED",
                        reason=f"Security violation: invalid path format '{val}': {e}",
                    )

        return PolicyCheckResult(
            allowed=True,
            status="APPROVED",
            sanitized_args=arguments,
        )
