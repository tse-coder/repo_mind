"""
intake_node — Initializes the investigation from a user query and repo path.

Resolves the snapshot identity (Git SHA or directory hash), sets budgets,
and populates the initial context fields of InvestigationState.
"""

import hashlib
import subprocess
import uuid
from pathlib import Path

from backend.agent.state import InvestigationState
from backend.config import DEFAULT_MAX_STEPS


def _resolve_sha(repo_path: str) -> str:
    """Return the Git HEAD SHA if the path is a git repo, else a directory content hash."""
    git_dir = Path(repo_path) / ".git"
    if git_dir.is_dir():
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()[:12]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    # Fallback: hash the top-level listing
    entries = sorted(str(p) for p in Path(repo_path).rglob("*") if p.is_file())
    digest = hashlib.sha256("\n".join(entries[:500]).encode()).hexdigest()
    return f"dir_{digest[:12]}"


def intake_node(state: InvestigationState) -> dict:
    """Initialize investigation context from the user's query and repo path."""
    repo_path = state["repo_path"]
    commit_sha = _resolve_sha(repo_path)

    return {
        "investigation_id": f"inv_{uuid.uuid4().hex[:8]}",
        "commit_sha": commit_sha,
        "artifact_type": None,
        "query_type": "",
        "entities": [],
        "needs_clarification": False,
        "evidence_slots": {},
        "contracts_store": [],
        "models_store": [],
        "plan": [],
        "plan_version": 0,
        "current_goal_id": None,
        "current_tool_call": None,
        "retry_ledger": {},
        "step_count": 0,
        "max_steps": DEFAULT_MAX_STEPS,
        "consecutive_no_progress": 0,
        "clarification_count": 0,
        "draft_answer": None,
        "final_answer": None,
        "limitations": [],
        "status": "RUNNING",
        "next_route": "classify",
    }
