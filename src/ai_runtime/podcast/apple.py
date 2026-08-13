"""
EasyChatBot Hackathon — Apple Podcasts catalogue provider.

Uses Apple's iTunes Search API for read-only podcast catalogue discovery.
"""

from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.ai_runtime.podcast.models import (
    PodcastProviderName,
    PodcastSearchIntent,
    PodcastSearchResult,
    normalise_language,
)


class ApplePodcastProvider:
    """Read-only Apple podcast catalogue provider."""

    BASE_URL = "https://itunes.apple.com/search"

    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        self._timeout_seconds = timeout_seconds

    def search(
        self,
        intent: PodcastSearchIntent,
    ) -> list[PodcastSearchResult]:
        query_terms = list(intent.topics) + list(intent.keywords)
        params = {
            "term": " ".join(query_terms[:6]),
            "country": intent.learning_context.country_code.upper(),
            "media": "podcast",
            "entity": "podcast",
            "limit": str(intent.max_results),
            "explicit": "No",
        }

        request = Request(
            f"{self.BASE_URL}?{urlencode(params)}",
            headers={
                "Accept": "application/json",
                "User-Agent": "EasyChatBot-Hackathon/1.0",
            },
            method="GET",
        )

        with urlopen(
            request,
            timeout=self._timeout_seconds,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        return [
            self._normalise(item)
            for item in payload.get("results", [])
            if self._is_podcast_result(item)
        ]

    @staticmethod
    def _is_podcast_result(item: dict[str, object]) -> bool:
        return (
            str(item.get("kind", "")).lower() == "podcast"
            or str(item.get("wrapperType", "")).lower() == "track"
        )

    @staticmethod
    def _normalise(
        item: dict[str, object],
    ) -> PodcastSearchResult:
        language = normalise_language(
            str(item.get("language") or "unknown")
        )

        return PodcastSearchResult(
            provider=PodcastProviderName.APPLE,
            external_id=str(
                item.get("collectionId")
                or item.get("trackId")
                or ""
            ),
            title=str(
                item.get("collectionName")
                or item.get("trackName")
                or ""
            ),
            description=str(
                item.get("description")
                or item.get("longDescription")
                or ""
            ),
            publisher=str(
                item.get("artistName")
                or "Unknown publisher"
            ),
            languages=(language,),
            url=str(
                item.get("collectionViewUrl")
                or item.get("trackViewUrl")
                or ""
            ),
            image_url=str(
                item.get("artworkUrl600")
                or item.get("artworkUrl100")
                or ""
            ) or None,
            published_at=str(
                item.get("releaseDate") or ""
            ) or None,
            explicit=(
                str(
                    item.get("trackExplicitness", "")
                ).lower() == "explicit"
            ),
            metadata={"provider": "apple_podcasts"},
        )
