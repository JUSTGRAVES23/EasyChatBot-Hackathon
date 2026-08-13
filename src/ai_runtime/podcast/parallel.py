"""
EasyChatBot Hackathon — Parallel Podcast Provider.

Provider adapter boundary for Parallel Search.

Responsibilities:

- implement PodcastProvider contract;
- translate provider responses;
- keep Parallel integration isolated.

Does NOT:

- implement Runtime logic;
- implement Agent logic;
- bypass CapabilityGateway;
- import Parallel SDK directly.

Architecture:

PodcastDiscoveryExecutor
        |
        v
PodcastProvider Protocol
        |
        v
ParallelPodcastProvider
        |
        v
Parallel Search Client
"""

from __future__ import annotations

from typing import Any

from src.ai_runtime.podcast.models import (
    PodcastProviderName,
    PodcastSearchIntent,
    PodcastSearchResult,
)


class ParallelPodcastProvider:
    """
    Parallel Search provider adapter.

    The real Parallel client is injected later.

    Without a client this adapter performs no search.
    """

    def __init__(
        self,
        client: Any | None = None,
    ) -> None:

        self._client = client


    @property
    def provider_id(
        self,
    ) -> str:
        """
        Stable provider identifier.
        """

        return "parallel"


    def search(
        self,
        intent: PodcastSearchIntent,
    ) -> list[PodcastSearchResult]:
        """
        Execute provider search.

        Sprint 0 behaviour:

        - no injected client:
            return []

        - injected client:
            map external response into
            provider-neutral contracts.
        """

        if self._client is None:
            return []


        response = self._client.search(
            intent,
        )


        return self._map_results(
            response,
        )


    def _map_results(
        self,
        response: list[dict[str, Any]],
    ) -> list[PodcastSearchResult]:
        """
        Convert Parallel response into
        provider-neutral Runtime models.
        """

        results: list[PodcastSearchResult] = []


        for item in response:

            results.append(
                PodcastSearchResult(
                    provider=(
                        PodcastProviderName.APPLE
                    ),

                    external_id=str(
                        item.get(
                            "id",
                            "parallel-result",
                        )
                    ),

                    title=str(
                        item.get(
                            "title",
                            "Unknown title",
                        )
                    ),

                    description=str(
                        item.get(
                            "description",
                            "",
                        )
                    ),

                    publisher=str(
                        item.get(
                            "publisher",
                            "Parallel",
                        )
                    ),

                    languages=tuple(
                        item.get(
                            "languages",
                            ["en"],
                        )
                    ),

                    url=str(
                        item.get(
                            "url",
                            "https://example.com",
                        )
                    ),

                    metadata={
                        "provider": "parallel",
                    },
                )
            )


        return results