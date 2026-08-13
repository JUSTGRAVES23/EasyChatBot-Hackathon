import json

from src.ai_runtime.podcast.apple import ApplePodcastProvider
from src.ai_runtime.podcast.models import (
    LearningContext,
    PodcastProviderName,
    PodcastSearchIntent,
)
from src.ai_runtime.podcast.spotify import SpotifyPodcastProvider


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def intent() -> PodcastSearchIntent:
    return PodcastSearchIntent(
        user_id="user-001",
        learning_context=LearningContext(
            world_id="French World",
            target_language="fr",
            learner_level="B2",
        ),
        topics=("artificial intelligence",),
    )


def test_apple_normalises_language(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.ai_runtime.podcast.apple.urlopen",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [
                    {
                        "kind": "podcast",
                        "collectionId": 123,
                        "collectionName": "IA en France",
                        "artistName": "Demo Publisher",
                        "language": "French",
                        "collectionViewUrl": (
                            "https://podcasts.apple.com/example"
                        ),
                    }
                ]
            }
        ),
    )

    results = ApplePodcastProvider().search(intent())

    assert len(results) == 1
    assert results[0].provider == PodcastProviderName.APPLE
    assert results[0].languages == ("fr",)


def test_spotify_normalises_episode_language(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.ai_runtime.podcast.spotify.urlopen",
        lambda *args, **kwargs: FakeResponse(
            {
                "episodes": {
                    "items": [
                        {
                            "id": "episode-001",
                            "name": "IA en Europe",
                            "description": "European AI regulation",
                            "languages": ["fr"],
                            "duration_ms": 1800000,
                            "release_date": "2026-08-10",
                            "external_urls": {
                                "spotify": (
                                    "https://open.spotify.com/episode/episode-001"
                                )
                            },
                            "images": [],
                        }
                    ]
                }
            }
        ),
    )

    results = SpotifyPodcastProvider(
        access_token="test-token"
    ).search(intent())

    assert len(results) == 1
    assert results[0].provider == PodcastProviderName.SPOTIFY
    assert results[0].languages == ("fr",)
    assert results[0].duration_seconds == 1800
