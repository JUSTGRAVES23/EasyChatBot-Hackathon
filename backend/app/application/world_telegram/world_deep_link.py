from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from app.application.world_catalogue.service import LearningWorldCatalogueService


@dataclass(frozen=True, slots=True)
class WorldNavigationMetadata:
    """Frontend navigation metadata for one Learning World."""

    world_id: str
    primary_language: str
    secondary_language: str

    def __post_init__(self) -> None:
        for field_name in (
            "world_id",
            "primary_language",
            "secondary_language",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required.")


class WorldDeepLinkBuilder:
    """Build non-authenticating links into the existing World frontend flow."""

    def __init__(self, *, frontend_base_url: str) -> None:
        base_url = frontend_base_url.strip()
        if not base_url:
            raise ValueError("frontend_base_url is required.")
        self._frontend_base_url = base_url.rstrip("/")

    def build(self, metadata: WorldNavigationMetadata) -> str:
        if not isinstance(metadata, WorldNavigationMetadata):
            raise TypeError("metadata must be WorldNavigationMetadata.")

        query = urlencode(
            {
                "world": metadata.world_id.strip(),
                "primaryLanguage": metadata.primary_language.strip(),
                "secondaryLanguage": metadata.secondary_language.strip(),
            }
        )
        return f"{self._frontend_base_url}/manifesto?{query}"


class TelegramWorldDeepLinkBuilder:
    """Build a non-authenticating Telegram deep link for a World.

    The payload is deliberately namespaced so it cannot be confused with the
    existing onboarding connection token handled by the Telegram start flow.
    W19.7 will consume the payload and perform routing.
    """

    _PREFIX = "world_"

    def __init__(self, *, telegram_bot_username: str) -> None:
        username = telegram_bot_username.strip().lstrip("@")
        if not username:
            raise ValueError("telegram_bot_username is required.")
        self._telegram_bot_username = username

    def build(self, *, world_identifier: str) -> str:
        identifier = world_identifier.strip()
        if not identifier:
            raise ValueError("world_identifier is required.")

        payload = f"{self._PREFIX}{identifier}"
        if len(payload.encode("utf-8")) > 64:
            raise ValueError("world deep-link payload exceeds Telegram's limit.")

        return f"https://t.me/{self._telegram_bot_username}?{urlencode({'start': payload})}"


class WorldDeepLinkService:
    """Validate catalogue identity before producing World navigation links.

    The catalogue remains authoritative for World identity and runtime
    configuration. This service never creates or consumes authentication
    tokens and never grants World access.
    """

    def __init__(
        self,
        *,
        catalogue_service: LearningWorldCatalogueService,
        frontend_link_builder: WorldDeepLinkBuilder,
        telegram_link_builder: TelegramWorldDeepLinkBuilder,
    ) -> None:
        if catalogue_service is None:
            raise ValueError("catalogue_service is required.")
        if frontend_link_builder is None:
            raise ValueError("frontend_link_builder is required.")
        if telegram_link_builder is None:
            raise ValueError("telegram_link_builder is required.")

        self._catalogue_service = catalogue_service
        self._frontend_link_builder = frontend_link_builder
        self._telegram_link_builder = telegram_link_builder

    def build_frontend_link(
        self,
        *,
        world_identifier: str,
        primary_language: str,
        secondary_language: str,
    ) -> str:
        entry = self._require_enabled_catalogue_entry(world_identifier)

        metadata = WorldNavigationMetadata(
            world_id=entry.identifier,
            primary_language=primary_language,
            secondary_language=secondary_language,
        )
        return self._frontend_link_builder.build(metadata)

    def build_telegram_link(self, *, world_identifier: str) -> str:
        entry = self._require_enabled_catalogue_entry(world_identifier)
        return self._telegram_link_builder.build(
            world_identifier=entry.identifier,
        )

    def _require_enabled_catalogue_entry(self, identifier: str):
        normalized = identifier.strip() if isinstance(identifier, str) else ""
        if not normalized:
            raise ValueError("world_identifier is required.")

        entry = self._catalogue_service.get_by_identifier(normalized)
        if entry is None:
            raise ValueError(f"Learning World not found: {normalized}")

        if not entry.enabled:
            raise ValueError(
                f"Learning World is disabled: {entry.identifier}"
            )

        if not entry.runtime_world_id:
            raise ValueError(
                f"Learning World has no runtime configuration: "
                f"{entry.identifier}"
            )

        return entry


__all__ = [
    "TelegramWorldDeepLinkBuilder",
    "WorldDeepLinkBuilder",
    "WorldDeepLinkService",
    "WorldNavigationMetadata",
]
