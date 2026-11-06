"""
InvestigationSession & InvestigationManager — handles graph execution lifecycle,
in-memory session state, human-in-the-loop interrupts/resumes, and fan-out SSE queues.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from backend.agent.graph import create_investigation_app
from backend.config import DEFAULT_MAX_STEPS
from backend.knowledge.snapshot import resolve_repo_path

logger = logging.getLogger("repomind.manager")


class InvestigationEvent:
    """Represents a single Server-Sent Event (SSE)."""

    def __init__(self, event: str, data: dict[str, Any]):
        self.event = event
        self.data = data
        self.timestamp = time.time()

    def to_sse_dict(self) -> dict[str, str]:
        """Convert to sse-starlette format."""
        return {
            "event": self.event,
            "data": json.dumps(self.data),
        }


class InvestigationSession:
    """Encapsulates the state and event streams for a single repository investigation."""

    def __init__(
        self,
        investigation_id: str,
        repo_path: str,
        query: str,
        max_steps: int,
    ):
        self.investigation_id = investigation_id
        self.thread_id = investigation_id
        self.repo_path = repo_path
        self.query = query
        self.max_steps = max_steps
        self.status = "INITIALIZED"  # INITIALIZED, RUNNING, PAUSED, COMPLETED, FAILED
        self.current_node: str | None = None
        self.state_values: dict[str, Any] = {}
        self.clarification_prompt: dict[str, Any] | None = None
        self.created_at = time.time()

        # Event storage and subscriber queues
        self.event_history: list[InvestigationEvent] = []
        self._subscribers: list[asyncio.Queue] = []
        self._lock = asyncio.Lock()
        self.background_task: asyncio.Task | None = None

    @property
    def is_finished(self) -> bool:
        """Return True if session reached a terminal status."""
        return self.status in {"COMPLETED", "FAILED", "SUFFICIENT", "PARTIAL"}

    async def emit_event(self, event_type: str, data: dict[str, Any]):
        """Append to history and dispatch to all active subscriber queues."""
        event = InvestigationEvent(event_type, data)
        async with self._lock:
            self.event_history.append(event)
            for queue in self._subscribers:
                await queue.put(event)

    async def subscribe(self) -> AsyncGenerator[dict[str, str], None]:
        """
        Subscribe to SSE events.
        Replays past events, then yields incoming real-time events.
        """
        queue: asyncio.Queue[InvestigationEvent | None] = asyncio.Queue()

        async with self._lock:
            # Replay all past events
            for past_event in self.event_history:
                await queue.put(past_event)

            # If already finished, signal end
            if self.is_finished:
                await queue.put(None)
            else:
                self._subscribers.append(queue)

        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event.to_sse_dict()
        finally:
            async with self._lock:
                if queue in self._subscribers:
                    self._subscribers.remove(queue)


class InvestigationManager:
    """Manages active investigation sessions and orchestrates the LangGraph engine."""

    def __init__(self):
        self._sessions: dict[str, InvestigationSession] = {}
        self.checkpointer = MemorySaver()
        self.app = create_investigation_app(checkpointer=self.checkpointer)

    def create_session(
        self,
        repo_path: str,
        query: str,
        max_steps: int | None = None,
        session_id: str | None = None,
    ) -> InvestigationSession:
        """Validate input, mint an investigation ID, and schedule background run."""
        resolved_path = resolve_repo_path(repo_path)
        if not resolved_path or not resolved_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
        if not resolved_path.is_dir():
            raise NotADirectoryError(f"Repository path is not a directory: {repo_path}")

        investigation_id = session_id or f"inv_{uuid.uuid4().hex[:8]}"
        steps = max_steps if max_steps is not None else DEFAULT_MAX_STEPS

        # If reusing an existing session ID, reset its event queue and state for follow-up
        existing = self._sessions.get(investigation_id)
        if existing:
            existing.query = query
            existing.max_steps = steps
            existing.status = "INITIALIZED"
            existing.event_history = []
            existing.clarification_prompt = None
            session = existing
        else:
            session = InvestigationSession(
                investigation_id=investigation_id,
                repo_path=str(resolved_path),
                query=query,
                max_steps=steps,
            )
            self._sessions[investigation_id] = session

        # Launch background graph run
        session.background_task = asyncio.create_task(
            self._execute_investigation(session, resume_value=None)
        )
        return session

    def get_session(self, investigation_id: str) -> InvestigationSession | None:
        """Retrieve an investigation session by ID."""
        return self._sessions.get(investigation_id)

    def resume_session(self, investigation_id: str, user_response: str) -> InvestigationSession:
        """Resume an investigation paused by clarify_node interrupt()."""
        session = self.get_session(investigation_id)
        if not session:
            raise KeyError(f"Investigation '{investigation_id}' not found.")
        if session.status != "PAUSED":
            raise ValueError(
                f"Investigation '{investigation_id}' is in status '{session.status}', cannot resume."
            )

        session.status = "RUNNING"
        session.clarification_prompt = None

        session.background_task = asyncio.create_task(
            self._execute_investigation(session, resume_value=user_response)
        )
        return session

    async def _execute_investigation(
        self,
        session: InvestigationSession,
        resume_value: str | None = None,
    ):
        """Execute or resume the investigation graph and emit structured SSE events."""
        session.status = "RUNNING"
        config = {
            "configurable": {"thread_id": session.thread_id},
            "run_name": f"RepoMind API: {session.investigation_id}",
        }

        try:
            if resume_value is not None:
                # Resume interrupted graph with user input
                stream_input = Command(resume=resume_value)
            else:
                # Initial run state matching InvestigationState
                stream_input = {
                    "repo_path": session.repo_path,
                    "query": session.query,
                    "max_steps": session.max_steps,
                    "step_count": 0,
                    "clarification_count": 0,
                    "consecutive_no_progress": 0,
                    "tool_history": [],
                    "evidence_store": [],
                    "findings": [],
                    "reflections": [],
                    "chat_history": [{"role": "user", "content": session.query}],
                    "evidence_slots": {},
                    "plan": [],
                    "plan_version": 1,
                    "retry_ledger": {},
                    "limitations": [],
                    "status": "RUNNING",
                }

            async for chunk in self.app.astream(
                stream_input,
                config=config,
                stream_mode="updates",
            ):
                for node_name, state_update in chunk.items():
                    session.current_node = node_name
                    session.state_values.update(state_update)

                    # 1. Node Change Event
                    await session.emit_event(
                        "node_change",
                        {
                            "node": node_name,
                            "investigation_id": session.investigation_id,
                        },
                    )

                    # 2. Plan Update Event
                    if state_update.get("plan"):
                        await session.emit_event(
                            "plan_update",
                            {
                                "plan": state_update["plan"],
                                "plan_version": state_update.get(
                                    "plan_version",
                                    session.state_values.get("plan_version", 1),
                                ),
                            },
                        )

                    # 3. Tool Call Event (when select_action proposes a tool)
                    if node_name == "select_action" and "current_tool_call" in state_update:
                        tc = state_update["current_tool_call"]
                        if tc:
                            await session.emit_event(
                                "tool_call",
                                {
                                    "tool": tc.get("tool_slug"),
                                    "arguments": tc.get("arguments", {}),
                                    "rationale": tc.get("rationale", ""),
                                },
                            )

                    # 4. Tool Result Event (when execute_tool finishes)
                    if state_update.get("tool_history"):
                        latest = state_update["tool_history"][-1]
                        summary = latest.get("output_summary") or latest.get("output") or ""
                        await session.emit_event(
                            "tool_result",
                            {
                                "tool": latest.get("tool_slug"),
                                "status": latest.get("status"),
                                "summary": summary[:2500],
                                "step": latest.get("step"),
                            },
                        )

                    # 5. Evidence & Findings Event (when observe finishes)
                    if state_update.get("evidence_store") or state_update.get("findings"):
                        await session.emit_event(
                            "evidence_update",
                            {
                                "evidence": state_update.get("evidence_store", []),
                                "findings": state_update.get("findings", []),
                            },
                        )

                    # 6. Reflection Event
                    if state_update.get("reflections"):
                        latest_ref = state_update["reflections"][-1]
                        await session.emit_event(
                            "reflection",
                            {
                                "trigger": latest_ref.get("trigger"),
                                "diagnosis": latest_ref.get("diagnosis"),
                                "next_approach": latest_ref.get("next_approach"),
                            },
                        )

                    # 7. Streaming Token Generation
                    if state_update.get("draft_answer"):
                        draft = state_update["draft_answer"]
                        if isinstance(draft, list) and len(draft) > 0 and isinstance(draft[0], dict):
                            draft = draft[0].get("text", str(draft))
                        draft_str = str(draft)
                        # Stream draft tokens in smooth bite-sized chunks
                        chunk_size = 12
                        for idx in range(0, len(draft_str), chunk_size):
                            await session.emit_event(
                                "token",
                                {"token": draft_str[idx : idx + chunk_size]},
                            )
                            await asyncio.sleep(0.012)

                    # 8. Final Answer
                    if state_update.get("final_answer"):
                        fin = state_update["final_answer"]
                        if isinstance(fin, list) and len(fin) > 0 and isinstance(fin[0], dict):
                            fin = fin[0].get("text", str(fin))
                        session.status = state_update.get("status", "COMPLETED")
                        await session.emit_event(
                            "done",
                            {
                                "status": session.status,
                                "final_answer": str(fin),
                                "limitations": state_update.get("limitations", []),
                            },
                        )

            # Check post-loop state
            state_snapshot = self.app.get_state(config)
            if state_snapshot.next:
                # Graph paused or has pending steps
                pass
            else:
                if not session.is_finished:
                    session.status = session.state_values.get("status", "COMPLETED")
                    fin = session.state_values.get("final_answer", "")
                    if isinstance(fin, list) and len(fin) > 0 and isinstance(fin[0], dict):
                        fin = fin[0].get("text", str(fin))
                    await session.emit_event(
                        "done",
                        {
                            "status": session.status,
                            "final_answer": str(fin) if fin else "Investigation concluded.",
                            "limitations": session.state_values.get("limitations", []),
                        },
                    )

        except GraphInterrupt:
            # LangGraph interrupt() called — save clarification prompt and pause
            state_snapshot = self.app.get_state(config)
            prompt_data = {"type": "clarification_request", "question": session.query}
            for task in state_snapshot.tasks:
                if task.interrupts:
                    for intr in task.interrupts:
                        if hasattr(intr, "value") and isinstance(intr.value, dict):
                            prompt_data = intr.value

            session.status = "PAUSED"
            session.clarification_prompt = prompt_data
            await session.emit_event("interrupt", prompt_data)

        except Exception as exc:
            logger.exception("Investigation '%s' failed", session.investigation_id)
            session.status = "FAILED"
            await session.emit_event(
                "error",
                {"error": str(exc), "investigation_id": session.investigation_id},
            )
            await session.emit_event(
                "done",
                {"status": "FAILED", "error": str(exc)},
            )

        finally:
            # If terminated, signal all subscribers that stream ended
            if session.is_finished:
                async with session._lock:
                    for queue in session._subscribers:
                        await queue.put(None)


# Global singleton manager instance
manager = InvestigationManager()
