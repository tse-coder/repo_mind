"""Database connection, LangGraph checkpointing, and domain persistence with Supabase PostgreSQL."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger("repomind.db")


class DatabaseManager:
    """Manages database connection pool, LangGraph checkpointer, and query execution."""

    def __init__(self):
        self.pool: AsyncConnectionPool | None = None
        self.checkpointer: BaseCheckpointSaver = MemorySaver()
        self._is_postgres: bool = False

    @property
    def is_postgres(self) -> bool:
        return self._is_postgres

    async def initialize(self) -> None:
        """Initialize connection pool, run schema migrations, and setup LangGraph checkpointer."""
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.info("DATABASE_URL not configured. Operating in local in-memory mode.")
            self.checkpointer = MemorySaver()
            self._is_postgres = False
            return

        try:
            logger.info("Connecting to PostgreSQL / Supabase...")
            # Supabase connection pooler or direct connection
            self.pool = AsyncConnectionPool(
                conninfo=db_url,
                max_size=10,
                open=False,
                kwargs={"autocommit": True, "row_factory": dict_row},
            )
            await self.pool.open()

            # Initialize LangGraph AsyncPostgresSaver
            postgres_saver = AsyncPostgresSaver(self.pool)
            await postgres_saver.setup()
            self.checkpointer = postgres_saver
            self._is_postgres = True
            logger.info("LangGraph AsyncPostgresSaver initialized successfully.")

            # Run initial migration tables if needed
            await self._run_migrations()
        except Exception:
            logger.exception("Failed to initialize PostgreSQL connection. Falling back to MemorySaver.")
            self.checkpointer = MemorySaver()
            self._is_postgres = False

    async def _run_migrations(self) -> None:
        """Run SQL migration file to create Better Auth and domain tables."""
        if not self.pool:
            return

        migration_file = Path(__file__).parent / "migrations" / "001_better_auth_and_repomind.sql"
        if not migration_file.exists():
            logger.warning("Migration file not found: %s", migration_file)
            return

        try:
            sql = migration_file.read_text(encoding="utf-8")
            async with self.pool.connection() as conn, conn.cursor() as cur:
                await cur.execute(sql)
            logger.info("Database migrations applied successfully.")
        except Exception as e:
            logger.warning("Error running database migrations: %s", e)

    async def close(self) -> None:
        """Close PostgreSQL connection pool gracefully."""
        if self.pool:
            logger.info("Closing PostgreSQL connection pool.")
            await self.pool.close()
            self.pool = None

    # ── Domain Persistence Methods ──────────────────────────────────────────────

    async def save_chat_session(
        self,
        chat_id: str,
        user_id: str | None,
        title: str,
        repo_path: str,
        max_steps: int = 15,
    ) -> None:
        """Insert or update a chat session."""
        if not self._is_postgres or not self.pool:
            return

        query = """
            INSERT INTO chat_sessions (id, user_id, title, repo_path, max_steps, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                repo_path = EXCLUDED.repo_path,
                max_steps = EXCLUDED.max_steps,
                updated_at = NOW();
        """
        try:
            async with self.pool.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, (chat_id, user_id, title, repo_path, max_steps))
        except Exception as e:
            logger.error("Failed to save chat session %s: %s", chat_id, e)

    async def list_chat_sessions(self, user_id: str) -> list[dict[str, Any]]:
        """List all chat sessions belonging to a user ordered by updated_at descending."""
        if not self._is_postgres or not self.pool:
            return []

        query = """
            SELECT id, user_id, title, repo_path, max_steps, created_at, updated_at
            FROM chat_sessions
            WHERE user_id = %s
            ORDER BY updated_at DESC;
        """
        try:
            async with self.pool.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, (user_id,))
                return await cur.fetchall()
        except Exception as e:
            logger.error("Failed to list chat sessions for user %s: %s", user_id, e)
            return []

    async def save_chat_message(
        self,
        message_id: str,
        chat_id: str,
        role: str,
        content: str,
        thoughts: list[dict[str, Any]] | None = None,
    ) -> None:
        """Save a chat message with associated thoughts to PostgreSQL."""
        if not self._is_postgres or not self.pool:
            return

        query = """
            INSERT INTO chat_messages (id, chat_id, role, content, thoughts, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                thoughts = EXCLUDED.thoughts;
        """
        thoughts_json = json.dumps(thoughts) if thoughts else None
        try:
            async with self.pool.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, (message_id, chat_id, role, content, thoughts_json))
        except Exception as e:
            logger.error("Failed to save chat message %s: %s", message_id, e)

    async def get_chat_messages(self, chat_id: str) -> list[dict[str, Any]]:
        """Fetch all messages for a given chat session."""
        if not self._is_postgres or not self.pool:
            return []

        query = """
            SELECT id, chat_id, role, content, thoughts, created_at
            FROM chat_messages
            WHERE chat_id = %s
            ORDER BY created_at ASC;
        """
        try:
            async with self.pool.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, (chat_id,))
                return await cur.fetchall()
        except Exception as e:
            logger.error("Failed to get messages for chat %s: %s", chat_id, e)
            return []

    async def save_investigation(
        self,
        inv_id: str,
        chat_id: str | None,
        user_id: str | None,
        status: str,
        query_text: str,
        findings: list[dict[str, Any]] | None = None,
        citations: list[dict[str, Any]] | None = None,
    ) -> None:
        """Persist or update an investigation record."""
        if not self._is_postgres or not self.pool:
            return

        sql = """
            INSERT INTO investigations (id, chat_id, user_id, status, query, findings, citations, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                findings = EXCLUDED.findings,
                citations = EXCLUDED.citations,
                updated_at = NOW();
        """
        findings_json = json.dumps(findings) if findings else None
        citations_json = json.dumps(citations) if citations else None
        try:
            async with self.pool.connection() as conn, conn.cursor() as cur:
                await cur.execute(
                    sql, (inv_id, chat_id, user_id, status, query_text, findings_json, citations_json)
                )
        except Exception as e:
            logger.error("Failed to save investigation %s: %s", inv_id, e)


# Global singleton database manager
db_manager = DatabaseManager()
