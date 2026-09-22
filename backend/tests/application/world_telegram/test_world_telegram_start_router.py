from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest

from app.application.world_telegram.world_telegram_start_router import (
    WORLD_START_PREFIX,
    WorldTelegramStartRouter,
)


@dataclass(frozen=True)
class FakeEntry:
    id: object
    identifier: str
    name: str
    description: str
    language: str
    version: str
    status: str
    enabled: bool
    world_type: str
    learning_domain: str
    runtime_world_id: str | None


class FakeCatalogueService:
    def __init__(self, entry: FakeEntry | None) -> None:
        self.entry = entry
        self.get_calls: list[str] = []
        self.resolve_calls: list[str] = []

    def get_by_identifier(self, identifier: str):
        self.get_calls.append(identifier)
        return self.entry

    def resolve_runtime_world(self, identifier: str):
        self.resolve_calls.append(identifier)
        if self.entry is None:
            raise ValueError("Learning World not found")
        if not self.entry.enabled:
            raise ValueError("Learning World is disabled")
        if not self.entry.runtime_world_id:
            raise ValueError("Learning World has no runtime configuration")
        return object()


def make_entry(**changes) -> FakeEntry:
    values = {
        "id": uuid4(),
        "identifier": "french",
        "name": "French World",
        "description": "French language learning world.",
        "language": "fr",
        "version": "1.0.0",
        "status": "published",
        "enabled": True,
        "world_type": "language",
        "learning_domain": "language_learning",
        "runtime_world_id": "french_world",
    }
    values.update(changes)
    return FakeEntry(**values)


def test_non_world_payload_is_left_for_connection_handler() -> None:
    catalogue = FakeCatalogueService(make_entry())
    router = WorldTelegramStartRouter(world_catalogue_service=catalogue)

    assert router.resolve("connection-token-123") is None
    assert catalogue.get_calls == []


@pytest.mark.parametrize(
    "payload",
    [
        None,
        "",
        "   ",
        "plain-token",
    ],
)
def test_non_world_payloads_are_not_routed(payload: str | None) -> None:
    catalogue = FakeCatalogueService(make_entry())
    router = WorldTelegramStartRouter(world_catalogue_service=catalogue)

    assert router.resolve(payload) is None


def test_world_payload_resolves_explicit_catalogue_mapping() -> None:
    catalogue = FakeCatalogueService(make_entry())
    router = WorldTelegramStartRouter(world_catalogue_service=catalogue)

    result = router.resolve(f"{WORLD_START_PREFIX}french")

    assert result is not None
    assert result.world_identifier == "french"
    assert result.runtime_world_id == "french_world"
    assert catalogue.get_calls == ["french"]
    assert catalogue.resolve_calls == ["french"]


def test_world_payload_is_trimmed() -> None:
    catalogue = FakeCatalogueService(make_entry())
    router = WorldTelegramStartRouter(world_catalogue_service=catalogue)

    result = router.resolve("  world_french  ")

    assert result is not None
    assert result.world_identifier == "french"


def test_empty_world_identifier_fails_closed() -> None:
    catalogue = FakeCatalogueService(make_entry())
    router = WorldTelegramStartRouter(world_catalogue_service=catalogue)

    with pytest.raises(ValueError, match="no World identifier"):
        router.resolve("world_")


def test_unknown_world_fails_closed() -> None:
    catalogue = FakeCatalogueService(None)
    router = WorldTelegramStartRouter(world_catalogue_service=catalogue)

    with pytest.raises(ValueError, match="not found"):
        router.resolve("world_unknown")


def test_disabled_world_fails_closed() -> None:
    catalogue = FakeCatalogueService(make_entry(enabled=False))
    router = WorldTelegramStartRouter(world_catalogue_service=catalogue)

    with pytest.raises(ValueError, match="disabled"):
        router.resolve("world_french")


def test_unconfigured_world_fails_closed() -> None:
    catalogue = FakeCatalogueService(make_entry(runtime_world_id=None))
    router = WorldTelegramStartRouter(world_catalogue_service=catalogue)

    with pytest.raises(ValueError, match="no runtime configuration"):
        router.resolve("world_french")


def test_router_does_not_authenticate_or_provision_access() -> None:
    catalogue = FakeCatalogueService(make_entry())
    router = WorldTelegramStartRouter(world_catalogue_service=catalogue)

    result = router.resolve("world_french")

    assert result is not None
    # The only observable interactions are catalogue reads/resolution.
    # No Telegram identity, access service, token service, or persistence
    # interface is present in this component.
