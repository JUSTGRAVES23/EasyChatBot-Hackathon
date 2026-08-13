"""
EasyChatBot Hackathon — podcast provider boundary.
"""

from __future__ import annotations

from typing import Protocol

from src.ai_runtime.podcast.models import (
    PodcastSearchIntent,
    PodcastSearchResult,
)


class PodcastProvider(Protocol):
    """
    Provider-independent catalogue interface.

    Apple and Spotify adapters implement this boundary; the Agent never
    depends on either provider.
    """

    def search(
        self,
        intent: PodcastSearchIntent,
    ) -> list[PodcastSearchResult]:
        """Search the provider catalogue using provider-neutral intent."""
        ...
