"""
Hackathon Memory persistence.

This module provides the minimal persistent Memory Store
required by the hackathon.

Architecture:

MemoryService
      |
      v
MemoryStore
      |
      v
SQLite

The store is deliberately small.

It is responsible only for persistence and retrieval of
MemoryEntry objects.

It does not:
- decide what should be remembered
- call an LLM
- perform semantic retrieval
- execute agents
- perform governance decisions
- manage purchases
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.ai_runtime.memory.models import (
    MemoryEntry,
    MemoryType,
)


class MemoryStore:
    """
    SQLite-backed persistence for hackathon memories.

    The database schema is created automatically when the
    store is initialised.
    """

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self._database_path = str(database_path)

        self._initialise_database()

    def _connect(self) -> sqlite3.Connection:
        """
        Create a SQLite connection.
        """

        connection = sqlite3.connect(
            self._database_path
        )

        connection.row_factory = sqlite3.Row

        return connection

    def _initialise_database(self) -> None:
        """
        Create the Memory table if it does not exist.
        """

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_memories_user_id
                ON memories(user_id)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_memories_user_type
                ON memories(user_id, memory_type)
                """
            )

    def save(
        self,
        memory: MemoryEntry,
    ) -> MemoryEntry:
        """
        Persist a MemoryEntry.

        Existing entries with the same memory_id are
        replaced.
        """

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO memories (
                    memory_id,
                    user_id,
                    memory_type,
                    content,
                    created_at,
                    updated_at,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.memory_id,
                    memory.user_id,
                    memory.memory_type.value,
                    memory.content,
                    memory.created_at.isoformat(),
                    memory.updated_at.isoformat(),
                    json.dumps(
                        memory.metadata,
                        ensure_ascii=False,
                    ),
                ),
            )

        return memory

    def get(
        self,
        memory_id: str,
    ) -> MemoryEntry | None:
        """
        Retrieve a single memory by identifier.
        """

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    memory_id,
                    user_id,
                    memory_type,
                    content,
                    created_at,
                    updated_at,
                    metadata_json
                FROM memories
                WHERE memory_id = ?
                """,
                (memory_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_memory(row)

    def list_for_user(
        self,
        user_id: str,
        memory_type: MemoryType | None = None,
    ) -> list[MemoryEntry]:
        """
        Retrieve memories belonging to a user.

        Results are returned newest first.
        """

        if not user_id.strip():
            raise ValueError(
                "Memory user_id cannot be empty."
            )

        with self._connect() as connection:

            if memory_type is None:
                rows = connection.execute(
                    """
                    SELECT
                        memory_id,
                        user_id,
                        memory_type,
                        content,
                        created_at,
                        updated_at,
                        metadata_json
                    FROM memories
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                    """,
                    (user_id,),
                ).fetchall()

            else:
                rows = connection.execute(
                    """
                    SELECT
                        memory_id,
                        user_id,
                        memory_type,
                        content,
                        created_at,
                        updated_at,
                        metadata_json
                    FROM memories
                    WHERE user_id = ?
                      AND memory_type = ?
                    ORDER BY updated_at DESC
                    """,
                    (
                        user_id,
                        memory_type.value,
                    ),
                ).fetchall()

        return [
            self._row_to_memory(row)
            for row in rows
        ]

    def delete(
        self,
        memory_id: str,
    ) -> bool:
        """
        Delete a memory.

        Returns True when a memory was deleted.
        """

        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM memories
                WHERE memory_id = ?
                """,
                (memory_id,),
            )

        return cursor.rowcount > 0

    @staticmethod
    def _row_to_memory(
        row: sqlite3.Row,
    ) -> MemoryEntry:
        """
        Convert a SQLite row into a MemoryEntry.
        """

        return MemoryEntry(
            memory_id=row["memory_id"],
            user_id=row["user_id"],
            memory_type=MemoryType(
                row["memory_type"]
            ),
            content=row["content"],
            created_at=(
                __import__("datetime")
                .datetime.fromisoformat(
                    row["created_at"]
                )
            ),
            updated_at=(
                __import__("datetime")
                .datetime.fromisoformat(
                    row["updated_at"]
                )
            ),
            metadata=json.loads(
                row["metadata_json"]
            ),
        )