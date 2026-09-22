from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest

from app.application.world_telegram.world_deep_link import (
    TelegramWorldDeepLinkBuilder,
    WorldDeepLinkBuilder,
    WorldDeepLinkService,
    WorldNavigationMetadata,
)


@dataclass(frozen=True)
class Entry:
    id: object
    identifier: str
    enabled: bool = True
    runtime_world_id: str | None = "french_world"


class FakeCatalogueService:
    def __init__(self, entry: Entry | None) -> None:
        self.entry = entry
        self.requested = []

    def get_by_identifier(self, identifier: str):
        self.requested.append(identifier)
        return self.entry


def make_service(entry: Entry | None = None) -> tuple[WorldDeepLinkService, FakeCatalogueService]:
    catalogue = FakeCatalogueService(
        entry
        or Entry(id=uuid4(), identifier="french"),
    )
    return (
        WorldDeepLinkService(
            catalogue_service=catalogue,
            frontend_link_builder=WorldDeepLinkBuilder(
                frontend_base_url="https://academy.example",
            ),
            telegram_link_builder=TelegramWorldDeepLinkBuilder(
                telegram_bot_username="@EasyChatBot",
            ),
        ),
        catalogue,
    )


def test_builds_existing_manifesto_contract() -> None:
    builder = WorldDeepLinkBuilder(
        frontend_base_url="http://localhost:3000/",
    )

    url = builder.build(
        WorldNavigationMetadata(
            world_id="french",
            primary_language="Français",
            secondary_language="English",
        )
    )

    assert (
        url
        == "http://localhost:3000/manifesto"
        "?world=french"
        "&primaryLanguage=Fran%C3%A7ais"
        "&secondaryLanguage=English"
    )


def test_builds_telegram_world_deep_link() -> None:
    builder = TelegramWorldDeepLinkBuilder(
        telegram_bot_username="@EasyChatBot",
    )

    assert (
        builder.build(world_identifier="french")
        == "https://t.me/EasyChatBot?start=world_french"
    )


def test_frontend_link_uses_canonical_catalogue_identifier() -> None:
    service, catalogue = make_service()

    result = service.build_frontend_link(
        world_identifier="french",
        primary_language="Français",
        secondary_language="English",
    )

    assert "world=french" in result
    assert catalogue.requested == ["french"]


def test_telegram_link_uses_canonical_catalogue_identifier() -> None:
    service, catalogue = make_service()

    result = service.build_telegram_link(world_identifier="french")

    assert result == "https://t.me/EasyChatBot?start=world_french"
    assert catalogue.requested == ["french"]


@pytest.mark.parametrize(
    "entry, expected",
    [
        (None, "not found"),
        (Entry(id=uuid4(), identifier="french", enabled=False), "disabled"),
        (
            Entry(id=uuid4(), identifier="french", runtime_world_id=None),
            "no runtime configuration",
        ),
    ],
)
def test_links_require_enabled_runtime_configured_world(
    entry: Entry | None,
    expected: str,
) -> None:
    service, _ = make_service(entry)

    with pytest.raises(ValueError, match=expected):
        service.build_telegram_link(world_identifier="french")


def test_telegram_builder_rejects_empty_identifier() -> None:
    builder = TelegramWorldDeepLinkBuilder(
        telegram_bot_username="EasyChatBot",
    )

    with pytest.raises(ValueError, match="world_identifier is required"):
        builder.build(world_identifier="   ")


def test_telegram_builder_rejects_payload_over_telegram_limit() -> None:
    builder = TelegramWorldDeepLinkBuilder(
        telegram_bot_username="EasyChatBot",
    )

    with pytest.raises(ValueError, match="exceeds Telegram"):
        builder.build(world_identifier="x" * 64)


def test_deep_links_never_create_connection_tokens() -> None:
    service, _ = make_service()

    frontend = service.build_frontend_link(
        world_identifier="french",
        primary_language="Français",
        secondary_language="English",
    )
    telegram = service.build_telegram_link(world_identifier="french")

    assert "token=" not in frontend
    assert "start=world_french" in telegram
    assert "start=" in telegram
