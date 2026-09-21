"""Application service for World Telegram learner memberships."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.domain.world_telegram import (
    TelegramMembershipStatus,
    WorldTelegramMembership,
)

from .membership_repositories import WorldTelegramMembershipRepository
from .repositories import WorldTelegramDestinationRepository


class WorldTelegramMembershipService:
    """Coordinate durable learner membership for a registered destination."""

    def __init__(
        self,
        *,
        repository: WorldTelegramMembershipRepository,
        destination_repository: WorldTelegramDestinationRepository,
    ) -> None:
        if repository is None:
            raise ValueError("repository cannot be None.")
        if destination_repository is None:
            raise ValueError("destination_repository cannot be None.")

        self._repository = repository
        self._destination_repository = destination_repository

    def register_membership(
        self,
        *,
        destination_id: UUID,
        user_id: UUID,
    ) -> WorldTelegramMembership:
        if not isinstance(destination_id, UUID):
            raise ValueError("destination_id must be a UUID.")
        if not isinstance(user_id, UUID):
            raise ValueError("user_id must be a UUID.")

        normalized_user_id = user_id

        destination = self._destination_repository.get_by_id(destination_id)
        if destination is None:
            raise ValueError(
                f"Telegram destination '{destination_id}' does not exist."
            )

        existing = self._repository.get_by_destination_and_user(
            destination_id=destination_id,
            user_id=normalized_user_id,
        )
        if existing is not None:
            raise ValueError(
                "Telegram membership is already registered for this "
                "destination and user."
            )

        now = datetime.now(timezone.utc)

        membership = WorldTelegramMembership(
            id=uuid4(),
            destination_id=destination.id,
            user_id=normalized_user_id,
            status=TelegramMembershipStatus.ACTIVE,
            joined_at=now,
            left_at=None,
            created_at=now,
            updated_at=now,
        )

        return self._repository.save(membership)

    def get_membership(
        self,
        membership_id: UUID,
    ) -> WorldTelegramMembership | None:
        return self._repository.get_by_id(membership_id)

    def get_membership_for_user(
        self,
        *,
        destination_id: UUID,
        user_id: UUID,
    ) -> WorldTelegramMembership | None:
        """
        Return the membership for a learner and Telegram destination.

        This is the application-service lookup used by higher-level
        World Telegram access orchestration. It does not grant access
        or change membership state.
        """
        if not isinstance(destination_id, UUID):
            raise ValueError("destination_id must be a UUID.")
        if not isinstance(user_id, UUID):
            raise ValueError("user_id must be a UUID.")

        return self._repository.get_by_destination_and_user(
            destination_id=destination_id,
            user_id=user_id,
        )

    def list_memberships(
        self,
        destination_id: UUID,
    ) -> tuple[WorldTelegramMembership, ...]:
        if not isinstance(destination_id, UUID):
            raise ValueError("destination_id must be a UUID.")

        return self._repository.list_by_destination(destination_id)

    def set_active(
        self,
        *,
        membership_id: UUID,
        active: bool,
    ) -> WorldTelegramMembership:
        membership = self._repository.get_by_id(membership_id)

        if membership is None:
            raise ValueError(
                f"Telegram membership '{membership_id}' does not exist."
            )

        now = datetime.now(timezone.utc)

        if active:
            updated = WorldTelegramMembership(
                id=membership.id,
                destination_id=membership.destination_id,
                user_id=membership.user_id,
                status=TelegramMembershipStatus.ACTIVE,
                joined_at=membership.joined_at,
                left_at=None,
                created_at=membership.created_at,
                updated_at=now,
            )
        else:
            updated = WorldTelegramMembership(
                id=membership.id,
                destination_id=membership.destination_id,
                user_id=membership.user_id,
                status=TelegramMembershipStatus.INACTIVE,
                joined_at=membership.joined_at,
                left_at=now,
                created_at=membership.created_at,
                updated_at=now,
            )

        return self._repository.save(updated)

    def delete_membership(self, membership_id: UUID) -> bool:
        return self._repository.delete(membership_id)