"""
Backend Runtime Execution Context.

This context remains compatible with existing backend agents,
providers and services while supporting memory and intelligence
enrichment.

The canonical governed AI Runtime has its own RuntimeContext.

This backend ExecutionContext is therefore retained as a
compatibility/application context and must not be confused with
the canonical Runtime execution model.

The context is immutable so application services can safely create
derived contexts with dataclasses.replace().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from intelligence.intelligence_context import (
    IntelligenceContext,
)
from src.ai_runtime.memory.context_builder import (
    MemoryContext,
)


@dataclass(frozen=True)
class ExecutionContext:
    """
    Immutable backend execution context used by existing
    integrations, agents and application services.

    The context carries execution metadata plus optional bounded
    learner memory and live-intelligence context.

    Context enrichment must use dataclasses.replace() rather than
    mutating an existing instance.
    """

    execution_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    user_id: str | None = None

    request: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    memory_context: MemoryContext | None = None

    intelligence_context: IntelligenceContext | None = None

    @property
    def has_memory_context(self) -> bool:
        """
        Return True when bounded learner memory is available.
        """
        return (
            self.memory_context is not None
            and not self.memory_context.is_empty
        )

    @property
    def has_intelligence_context(self) -> bool:
        """
        Return True when live intelligence is available.
        """
        return self.intelligence_context is not None

