"""
Runtime Execution Context.

Provides immutable runtime context shared with agents.

Responsibilities:
- identify an execution
- carry user request information
- provide runtime metadata
- optionally carry live intelligence context
- optionally carry bounded learner memory context

Does not:
- execute providers
- manage memory persistence
- modify systems
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.ai_runtime.memory.context_builder import (
    MemoryContext,
)


@dataclass(frozen=True)
class ExecutionContext:
    """
    Runtime execution context shared with agents.

    The context is immutable. Enrichment must therefore use
    dataclasses.replace() rather than mutating an existing
    instance.
    """

    user_id: str

    request: str

    execution_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    intelligence_context: Any | None = None

    memory_context: MemoryContext | None = None

    @property
    def has_intelligence_context(self) -> bool:
        """
        Return whether live intelligence is attached.
        """

        return (
            self.intelligence_context is not None
        )

    @property
    def has_memory_context(self) -> bool:
        """
        Return whether bounded learner memory context
        is attached.
        """

        return (
            self.memory_context is not None
            and not self.memory_context.is_empty
        )