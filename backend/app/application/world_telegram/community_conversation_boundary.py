"""Application boundary for learner conversations in World Telegram groups."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.services.world_access_service import WorldAccessService
from app.application.world_catalogue.repositories import (
    LearningWorldCatalogueRepository,
)
from app.application.world_telegram.membership_service import (
    WorldTelegramMembershipService,
)
from app.application.world_telegram.repositories import (
    WorldTelegramDestinationRepository,
)
from app.domain.world_telegram import (
    TelegramDestinationType,
    TelegramMembershipStatus,
)


MAX_TELEGRAM_COMMUNITY_MESSAGE_LENGTH = 4096
SUPPORTED_COMMUNITY_CHAT_TYPES = frozenset({"group", "supergroup"})


class WorldTelegramCommunityConversationError(ValueError):
    """Expected community conversation boundary failure."""


class WorldTelegramCommunityChatTypeError(
    WorldTelegramCommunityConversationError,
):
    """The Telegram chat is not a supported group conversation."""


class WorldTelegramCommunityDestinationNotFoundError(
    WorldTelegramCommunityConversationError,
):
    """The Telegram group is not registered for the requested World."""


class WorldTelegramCommunityDestinationDisabledError(
    WorldTelegramCommunityConversationError,
):
    """The registered Telegram group destination is disabled."""


@dataclass(frozen=True, slots=True)
class WorldTelegramCommunityConversationContext:
    """Authorized context passed to the future community conversation runtime."""

    user_id: UUID
    world_id: UUID
    destination_id: UUID
    telegram_chat_id: str
    message: str


class WorldTelegramCommunityConversationBoundary:
    """
    Authorize one learner message for a registered World Telegram group.

    W19.4 deliberately stops at the application conversation boundary.

    This class:
    - validates the community transport contract;
    - binds the message to the exact registered World destination;
    - verifies authoritative World entitlement;
    - verifies durable W19.2 learner membership;
    - returns a controlled context for W19.5+ runtime integration.

    This class does NOT:
    - call Telegram;
    - call an LLM/provider;
    - execute AI runtime;
    - create membership;
    - grant World access;
    - modify private-chat behaviour.
    """

    def __init__(
        self,
        *,
        world_access_service: WorldAccessService,
        world_catalogue_repository: LearningWorldCatalogueRepository,
        destination_repository: WorldTelegramDestinationRepository,
        membership_service: WorldTelegramMembershipService,
    ) -> None:
        if world_access_service is None:
            raise ValueError("world_access_service is required.")
        if world_catalogue_repository is None:
            raise ValueError("world_catalogue_repository is required.")
        if destination_repository is None:
            raise ValueError("destination_repository is required.")
        if membership_service is None:
            raise ValueError("membership_service is required.")

        self._world_access_service = world_access_service
        self._world_catalogue_repository = world_catalogue_repository
        self._destination_repository = destination_repository
        self._membership_service = membership_service

    def authorize_message(
        self,
        *,
        user_id: UUID,
        world_id: UUID,
        telegram_chat_id: str,
        chat_type: str,
        message: str,
    ) -> WorldTelegramCommunityConversationContext:
        """Authorize a learner message without invoking AI/runtime side effects."""
        self._validate_uuid(user_id, "user_id")
        self._validate_uuid(world_id, "world_id")

        if chat_type not in SUPPORTED_COMMUNITY_CHAT_TYPES:
            raise WorldTelegramCommunityChatTypeError(
                "Community conversation is only available in Telegram "
                "group or supergroup chats."
            )

        normalized_chat_id = self._validate_chat_id(telegram_chat_id)
        normalized_message = self._validate_message(message)

        world = self._world_catalogue_repository.get_by_id(world_id)
        if world is None:
            raise ValueError(
                f"Learning World '{world_id}' does not exist."
            )

        destination = self._destination_repository.get_by_world_and_chat(
            world_id=world_id,
            telegram_chat_id=normalized_chat_id,
        )

        if destination is None:
            raise WorldTelegramCommunityDestinationNotFoundError(
                "The Telegram group is not registered for this Learning World."
            )

        if destination.destination_type is not TelegramDestinationType.GROUP:
            raise WorldTelegramCommunityChatTypeError(
                "The registered Telegram destination is not a group."
            )

        if not destination.enabled:
            raise WorldTelegramCommunityDestinationDisabledError(
                "The registered Telegram group destination is disabled."
            )

        world_access = self._world_access_service.get_access(
            user_id=user_id,
            world_identifier=world.identifier,
        )

        if world_access is None or not world_access.is_active():
            raise PermissionError(
                "Learner does not have active access to this Learning World."
            )

        membership = self._membership_service.get_membership_for_user(
            destination_id=destination.id,
            user_id=user_id,
        )

        if (
            membership is None
            or membership.status is not TelegramMembershipStatus.ACTIVE
        ):
            raise PermissionError(
                "Learner does not have active membership in this "
                "World Telegram community."
            )

        return WorldTelegramCommunityConversationContext(
            user_id=user_id,
            world_id=world_id,
            destination_id=destination.id,
            telegram_chat_id=normalized_chat_id,
            message=normalized_message,
        )

    @staticmethod
    def _validate_uuid(value: UUID, field_name: str) -> None:
        if not isinstance(value, UUID):
            raise ValueError(f"{field_name} must be a UUID.")

    @staticmethod
    def _validate_chat_id(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("telegram_chat_id is required.")

        normalized = value.strip()

        if len(normalized) > 255:
            raise ValueError(
                "telegram_chat_id cannot exceed 255 characters."
            )

        return normalized

    @staticmethod
    def _validate_message(value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("message must be a string.")

        normalized = value.strip()

        if not normalized:
            raise ValueError("message cannot be empty.")

        if len(normalized) > MAX_TELEGRAM_COMMUNITY_MESSAGE_LENGTH:
            raise ValueError(
                "message exceeds the Telegram community message limit."
            )

        return normalized


__all__ = [
    "MAX_TELEGRAM_COMMUNITY_MESSAGE_LENGTH",
    "SUPPORTED_COMMUNITY_CHAT_TYPES",
    "WorldTelegramCommunityChatTypeError",
    "WorldTelegramCommunityConversationBoundary",
    "WorldTelegramCommunityConversationContext",
    "WorldTelegramCommunityConversationError",
    "WorldTelegramCommunityDestinationDisabledError",
    "WorldTelegramCommunityDestinationNotFoundError",
]
