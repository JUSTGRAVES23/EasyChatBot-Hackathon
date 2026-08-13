"""
EasyChatBot Hackathon — Podcast Discovery Agent.

The Agent converts explicit learner context and preference memory into
provider-neutral search intent.

It does not call Apple/Spotify, write memory, select a provider, or invent
podcast metadata.
"""

from __future__ import annotations

import re

from src.ai_runtime.memory.models import MemoryEntry, MemoryType
from src.ai_runtime.podcast.models import (
    LearningContext,
    PodcastSearchIntent,
)


class PodcastDiscoveryAgent:
    """Build provider-neutral podcast discovery intent."""

    _STOP_WORDS = {
        "a", "an", "and", "are", "be", "for", "from", "i", "in", "is",
        "like", "of", "on", "podcasts", "prefers", "prefer", "the", "to",
        "with", "you", "your",
    }

    def build_search_intent(
        self,
        *,
        user_id: str,
        learning_context: LearningContext,
        memories: list[MemoryEntry],
        max_results: int = 10,
    ) -> PodcastSearchIntent:
        """
        Convert explicit preferences + learning-world context into intent.

        Only PREFERENCE memories are used, matching the existing
        EasyChatBot discovery contract.
        """

        if not user_id.strip():
            raise ValueError("Podcast Agent user_id cannot be empty.")

        preferences = [
            memory
            for memory in memories
            if memory.user_id == user_id
            and memory.memory_type == MemoryType.PREFERENCE
        ]

        topics: list[str] = []
        keywords: list[str] = []

        for memory in preferences:
            topics.extend(
                self._metadata_terms(
                    memory.metadata,
                    "topics",
                    "interests",
                    "preferred_topics",
                )
            )
            keywords.extend(
                self._metadata_terms(
                    memory.metadata,
                    "keywords",
                )
            )

            if not topics and not keywords:
                keywords.extend(
                    self._content_keywords(memory.content)
                )

        # The learning world is always part of the search context.
        topics.append(learning_context.world_id)

        # Target language is deliberately a hard eligibility constraint,
        # not just another search keyword.
        return PodcastSearchIntent(
            user_id=user_id,
            learning_context=learning_context,
            topics=tuple(self._dedupe(topics)),
            keywords=tuple(self._dedupe(keywords)),
            language_required=True,
            max_results=max_results,
        )

    @staticmethod
    def _metadata_terms(
        metadata: dict[str, str],
        *keys: str,
    ) -> list[str]:
        terms: list[str] = []
        for key in keys:
            raw = metadata.get(key, "")
            if raw:
                terms.extend(
                    item.strip()
                    for item in re.split(r"[,;|]", raw)
                    if item.strip()
                )
        return terms

    @classmethod
    def _content_keywords(cls, content: str) -> list[str]:
        words = re.findall(
            r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9'-]{2,}",
            content.lower(),
        )
        return [
            word for word in words
            if word not in cls._STOP_WORDS
        ][:8]

    @staticmethod
    def _dedupe(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            key = value.strip().lower()
            if key and key not in seen:
                seen.add(key)
                result.append(value.strip())
        return result
