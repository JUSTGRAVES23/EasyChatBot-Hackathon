"""Application service for controlled World Telegram community access."""

from __future__ import annotations

from uuid import UUID

from app.application.services.world_access_service import (
    WorldAccessService,
)
from app.application.world_catalogue.repositories import (
    LearningWorldCatalogueRepository,
)
from app.domain.world_telegram import (
    TelegramMembershipStatus,
    WorldTelegramMembership,
)

from .membership_service import WorldTelegramMembershipService
from .repositories import WorldTelegramDestinationRepository


class WorldTelegramCommunityAccessError(ValueError):
    """Expected World Telegram community access failure."""


class WorldTelegramDestinationNotFoundError(
    WorldTelegramCommunityAccessError,
):
    """No Telegram destination is registered for the World."""


class WorldTelegramDestinationDisabledError(
    WorldTelegramCommunityAccessError,
):
    """The registered Telegram destination is disabled."""


class WorldTelegramCommunityAccessService:
    """
    Coordinate authorized learner access to a World Telegram community.

    World authorization remains owned by WorldAccessService.

    World identity remains owned by the authoritative
    LearningWorldCatalogueRepository.

    Telegram destination registration remains owned by the
    WorldTelegramDestinationRepository.

    Telegram membership state remains owned by
    WorldTelegramMembershipService.

    This service does not grant World access and does not call Telegram.
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

    def ensure_membership(
        self,
        *,
        user_id: UUID,
        world_id: UUID,
    ) -> WorldTelegramMembership:
        """
        Ensure an entitled learner has active membership for a World
        Telegram destination.

        The operation is idempotent:

        - existing ACTIVE membership is returned unchanged;
        - existing INACTIVE membership is reactivated;
        - missing membership is created as ACTIVE.

        World access is never granted by this operation.

        No Telegram API call is performed by this service.
        """
        self._validate_uuid(user_id, "user_id")
        self._validate_uuid(world_id, "world_id")

        world = self._world_catalogue_repository.get_by_id(world_id)

        if world is None:
            raise ValueError(
                f"Learning World '{world_id}' does not exist."
            )

        world_access = self._world_access_service.get_access(
            user_id=user_id,
            world_identifier=world.identifier,
        )

        if world_access is None or not world_access.is_active():
            raise PermissionError(
                "Learner does not have active access to this Learning World."
            )

        destinations = self._destination_repository.list_by_world(world_id)

        if not destinations:
            raise WorldTelegramDestinationNotFoundError(
                f"No Telegram destination is registered for "
                f"World '{world_id}'."
            )

        enabled_destinations = tuple(
            destination
            for destination in destinations
            if destination.enabled
        )

        if not enabled_destinations:
            raise WorldTelegramDestinationDisabledError(
                f"All Telegram destinations registered for "
                f"World '{world_id}' are disabled."
            )

        destination = enabled_destinations[0]

        existing = self._membership_service.get_membership_for_user(
            destination_id=destination.id,
            user_id=user_id,
        )

        if existing is None:
            return self._membership_service.register_membership(
                destination_id=destination.id,
                user_id=user_id,
            )

        if existing.status is TelegramMembershipStatus.ACTIVE:
            return existing

        return self._membership_service.set_active(
            membership_id=existing.id,
            active=True,
        )

    @staticmethod
    def _validate_uuid(
        value: UUID,
        field_name: str,
    ) -> None:
        if not isinstance(value, UUID):
            raise ValueError(f"{field_name} must be a UUID.")


__all__ = [
    "WorldTelegramCommunityAccessError",
    "WorldTelegramCommunityAccessService",
    "WorldTelegramDestinationDisabledError",
    "WorldTelegramDestinationNotFoundError",
]