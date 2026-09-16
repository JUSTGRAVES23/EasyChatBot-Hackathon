"""
EasyChatBot — Memory Context Builder.

H3-01 — Memory-Aware Live Intelligence.

The builder operates on the APPLICATION memory contract:

    MemoryService
        ↓
    MemoryRecord
        ↓
    MemoryContextBuilder
        ↓
    MemoryContext

It deliberately does NOT consume MemoryEntry directly.

MemoryEntry belongs to the persistence/runtime storage boundary.
MemoryRecord is the application-facing memory contract.

Responsibilities:
- validate already-retrieved memory
- enforce user isolation
- determine deterministic relevance
- bound memory count
- bound context size
- produce provider-independent context

Does not:
- retrieve memory
- persist memory
- call an LLM
- call a provider
- execute an agent
- mutate ExecutionContext
- perform semantic/vector search
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from memory.memory_record import (
    MemoryRecord,
)


DEFAULT_MAX_MEMORY_ITEMS = 5
DEFAULT_MAX_CONTEXT_CHARACTERS = 4000

_WORD_PATTERN = re.compile(
    r"[\wÀ-ÿ'-]+",
    re.UNICODE,
)


# Application-level memory categories.
#
# These are deliberately strings because MemoryService exposes
# MemoryRecord.category rather than MemoryEntry.memory_type.
_MEMORY_CATEGORY_PRIORITY: dict[str, int] = {
    "preference": 30,
    "learning_goal": 30,
    "discovery_context": 20,
    "saved_item": 10,
    "conversation": 10,
}


@dataclass(frozen=True)
class MemoryContext:
    """
    Bounded, provider-independent learner context.
    """

    entries: tuple[MemoryRecord, ...]
    text: str

    @property
    def is_empty(self) -> bool:
        """Return True when no memory was selected."""
        return not self.entries

    @property
    def memory_count(self) -> int:
        """Return the number of selected memories."""
        return len(self.entries)


class MemoryContextBuilder:
    """
    Build bounded learner context from MemoryRecord objects.

    The builder is stateless and deterministic.
    """

    def __init__(
        self,
        *,
        max_memory_items: int = DEFAULT_MAX_MEMORY_ITEMS,
        max_context_characters: int = (
            DEFAULT_MAX_CONTEXT_CHARACTERS
        ),
    ) -> None:
        if max_memory_items < 1:
            raise ValueError(
                "max_memory_items must be greater than zero."
            )

        if max_context_characters < 1:
            raise ValueError(
                "max_context_characters must be greater than zero."
            )

        self._max_memory_items = max_memory_items
        self._max_context_characters = (
            max_context_characters
        )

    def build(
        self,
        *,
        user_id: str,
        request: str,
        memories: list[MemoryRecord]
        | tuple[MemoryRecord, ...],
    ) -> MemoryContext:
        """
        Build bounded learner context.

        Memory is supplied by the caller.

        The builder does not retrieve or persist memory.
        """

        if not user_id.strip():
            raise ValueError(
                "user_id cannot be empty."
            )

        if not request.strip():
            raise ValueError(
                "request cannot be empty."
            )

        if not memories:
            return MemoryContext(
                entries=(),
                text="",
            )

        request_tokens = self._tokens(
            request
        )

        candidates: list[
            tuple[
                int,
                datetime,
                str,
                MemoryRecord,
            ]
        ] = []

        for memory in memories:

            if not isinstance(
                memory,
                MemoryRecord,
            ):
                continue

            # Defence in depth.
            if memory.user_id != user_id:
                continue

            if not memory.category.strip():
                continue

            if not memory.content.strip():
                continue

            score = self._score(
                memory=memory,
                request_tokens=request_tokens,
            )

            # A memory category alone does NOT make the memory
            # relevant to the current request.
            if score <= 0:
                continue

            candidates.append(
                (
                    score,
                    memory.created_at,
                    memory.content,
                    memory,
                )
            )

        # Deterministic ordering:
        #
        # 1. relevance descending
        # 2. newest memory first
        # 3. content as stable tie-breaker
        candidates.sort(
            key=lambda item: (
                -item[0],
                -item[1].timestamp(),
                item[2].casefold(),
            )
        )

        selected: list[MemoryRecord] = []
        rendered_items: list[str] = []

        current_length = len(
            "Learner context:\n"
        )

        for (
            _score,
            _created_at,
            _content,
            memory,
        ) in candidates:

            if (
                len(selected)
                >= self._max_memory_items
            ):
                break

            line = self._render_memory(
                memory
            )

            separator_length = (
                1
                if rendered_items
                else 0
            )

            projected_length = (
                current_length
                + separator_length
                + len(line)
            )

            if (
                projected_length
                > self._max_context_characters
            ):
                # Do not partially truncate an individual
                # memory because that could alter meaning.
                continue

            selected.append(memory)
            rendered_items.append(line)

            current_length = projected_length

        if not selected:
            return MemoryContext(
                entries=(),
                text="",
            )

        text = (
            "Learner context:\n"
            + "\n".join(
                f"- {item}"
                for item in rendered_items
            )
        )

        if (
            len(text)
            > self._max_context_characters
        ):
            raise AssertionError(
                "MemoryContextBuilder produced "
                "an oversized context."
            )

        return MemoryContext(
            entries=tuple(selected),
            text=text,
        )

    @staticmethod
    def _tokens(
        value: str,
    ) -> set[str]:
        """
        Return normalised tokens for deterministic matching.
        """

        return {
            token.casefold()
            for token in _WORD_PATTERN.findall(
                value
            )
            if len(token) > 1
        }

    @classmethod
    def _score(
        cls,
        *,
        memory: MemoryRecord,
        request_tokens: set[str],
    ) -> int:
        """
        Calculate deterministic relevance.

        Relevance requires actual token overlap.

        This prevents an unrelated preference such as
        "Prefers hiking" from being injected into a request
        about "European AI regulation" simply because it is
        a preference.
        """

        content_tokens = cls._tokens(
            memory.content
        )

        category_tokens = cls._tokens(
            memory.category
        )

        overlap = request_tokens & (
            content_tokens
            | category_tokens
        )

        if not overlap:
            return 0

        category = (
            memory.category.strip().casefold()
        )

        category_priority = (
            _MEMORY_CATEGORY_PRIORITY.get(
                category,
                10,
            )
        )

        return (
            category_priority
            + len(overlap)
        )

    @staticmethod
    def _render_memory(
        memory: MemoryRecord,
    ) -> str:
        """
        Render memory explicitly as learner context.

        Memory content is treated as data, not instructions.
        """

        category = (
            memory.category.strip()
        )

        content = " ".join(
            memory.content.split()
        )

        return (
            f"[{category}] {content}"
        )