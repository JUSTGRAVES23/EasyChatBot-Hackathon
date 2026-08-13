"""
EasyChatBot Hackathon — Spotify podcast catalogue provider.

The MVP searches episodes, because episode metadata exposes a `languages`
field. This allows EasyChatBot's language-learning rule to remain strict.

Credentials are injected as an access token; this module does not manage
OAuth state or user accounts.
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


class SpotifyPodcastProvider:
    """Read-only Spotify catalogue provider."""

    BASE_URL = "https://api.spotify.com/v1/search"

    def __init__(
        self,
        *,
        access_token: str,
        timeout_seconds: float = 10.0,
        market: str | None = None,
    ) -> None:
        if not access_token.strip():
            raise ValueError(
                "SpotifyPodcastProvider access_token cannot be empty."
            )
        self._access_token = access_token
        self._timeout_seconds = timeout_seconds
        self._market = market

    def search(
        self,
        intent: PodcastSearchIntent,
    ) -> list[PodcastSearchResult]:
        query_terms = list(intent.topics) + list(intent.keywords)
        params = {
            "q": " ".join(query_terms[:6]),
            "type": "episode",
            "limit": str(intent.max_results),
        }

        market = self._market or intent.learning_context.country_code
        if market:
            params["market"] = market.upper()

        request = Request(
            f"{self.BASE_URL}?{urlencode(params)}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self._access_token}",
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

        episodes = payload.get("episodes", {})
        if not isinstance(episodes, dict):
            return []

        items = episodes.get("items", [])
        if not isinstance(items, list):
            return []

        results: list[PodcastSearchResult] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            result = self._normalise_episode(item)
            if result is not None:
                results.append(result)

        return results

    @staticmethod
    def _normalise_episode(
        item: dict[str, object],
    ) -> PodcastSearchResult | None:
        external_id = str(item.get("id") or "")
        title = str(item.get("name") or "")

        external_urls = item.get("external_urls")
        url = ""
        if isinstance(external_urls, dict):
            url = str(
                external_urls.get("spotify") or ""
            )

        if not external_id or not title or not url:
            return None

        raw_languages = item.get("languages", [])
        if not isinstance(raw_languages, list):
            return None

        languages = tuple(
            normalise_language(str(language))
            for language in raw_languages
            if str(language).strip()
        )

        # Unknown language is not invented. The recommendation service
        # will reject a candidate if language_required=True.
        if not languages:
            return None

        images = item.get("images", [])
        image_url = None
        if isinstance(images, list) and images:
            first = images[0]
            if isinstance(first, dict):
                image_url = str(first.get("url") or "") or None

        duration_ms = item.get("duration_ms")
        duration_seconds = (
            int(duration_ms) // 1000
            if isinstance(duration_ms, (int, float))
            else None
        )

        return PodcastSearchResult(
            provider=PodcastProviderName.SPOTIFY,
            external_id=external_id,
            title=title,
            description=str(item.get("description") or ""),
            publisher="Spotify Podcast",
            languages=languages,
            url=url,
            image_url=image_url,
            published_at=str(
                item.get("release_date") or ""
            ) or None,
            duration_seconds=duration_seconds,
            explicit=bool(item.get("explicit", False)),
            metadata={
                "provider": "spotify",
                "content_type": "episode",
            },
        )
