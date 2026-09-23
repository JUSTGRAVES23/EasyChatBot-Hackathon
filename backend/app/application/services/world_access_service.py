"""Application service for learner-to-learning-world authorization."""

from __future__ import annotations

import asyncio
from typing import Protocol
from uuid import UUID

from app.domain.learning.learner_world_access import BETA, LearnerWorldAccess
from app.domain.learning.learner_world_access_repository import (
    LearnerWorldAccessRepository,
)


class CanonicalUserIdentityReader(Protocol):
    """Minimal provider-neutral read boundary over canonical user identity."""

    async def get_user_for_identity(self, user_id: UUID):
        """Return the canonical user record or None."""
        ...


class WorldAccessError(ValueError):
    """Expected World access validation failure."""


class UserNotFoundError(WorldAccessError):
    """The requested canonical user does not exist."""


class LearningWorldNotFoundError(WorldAccessError):
    """The requested Learning World does not exist."""


class LearningWorldDisabledError(WorldAccessError):
    """The requested Learning World is disabled for ordinary new grants."""


class WorldAccessService:
    """
    Authorize learners for one or more Learning Worlds.

    Important boundary:
    - World access is durable authorization/membership.
    - World ``enabled`` remains runtime availability.
    - Ordinary direct grants still reject disabled Worlds.
    - The explicit ``allow_disabled_world`` flag is reserved for a
      higher-level provisioning policy such as Beta portfolio provisioning.
    """

    def __init__(
        self,
        *,
        access_repository: LearnerWorldAccessRepository,
        user_identity_reader: CanonicalUserIdentityReader,
        learning_world_repository,
    ) -> None:
        if access_repository is None:
            raise ValueError("access_repository is required.")
        if user_identity_reader is None:
            raise ValueError("user_identity_reader is required.")
        if learning_world_repository is None:
            raise ValueError("learning_world_repository is required.")

        self._access_repository = access_repository
        self._user_identity_reader = user_identity_reader
        self._learning_world_repository = learning_world_repository

    async def grant_access(
        self,
        *,
        user_id: UUID,
        world_identifier: str,
        access_source: str = BETA,
        allow_disabled_world: bool = False,
    ) -> LearnerWorldAccess:
        self._validate_user_id(user_id)
        identifier = self._normalize_world_identifier(world_identifier)

        user = await self._user_identity_reader.get_user_for_identity(user_id)
        if user is None:
            raise UserNotFoundError("Canonical user does not exist.")

        world = await asyncio.to_thread(
            self._learning_world_repository.get_by_identifier,
            identifier,
        )

        if world is None:
            raise LearningWorldNotFoundError(
                f"Learning World does not exist: {identifier}"
            )

        if not world.enabled and not allow_disabled_world:
            raise LearningWorldDisabledError(
                f"Learning World is disabled: {identifier}"
            )

        world_id = self._world_id(world)

        existing = await asyncio.to_thread(
            self._access_repository.get_by_user_and_world,
            user_id=user_id,
            world_id=world_id,
        )

        if existing is not None:
            if existing.is_active():
                return existing

            revived = LearnerWorldAccess.grant(
                user_id=user_id,
                world_id=world_id,
                access_source=access_source,
                access_id=existing.access_id,
            )
            return await asyncio.to_thread(
                self._access_repository.save,
                revived,
            )

        access = LearnerWorldAccess.grant(
            user_id=user_id,
            world_id=world_id,
            access_source=access_source,
        )

        return await asyncio.to_thread(
            self._access_repository.save,
            access,
        )

    async def revoke_access(
        self,
        *,
        user_id: UUID,
        world_identifier: str,
        access_source: str | None = None,
    ) -> LearnerWorldAccess | None:
        """Revoke durable World access without deleting its history.

        When ``access_source`` is supplied, only access originating from
        that source is revoked.

        This prevents subscription lifecycle changes from accidentally
        revoking independent Beta or Admin access.

        The operation is idempotent:
        - no record -> None;
        - already revoked -> existing record;
        - active matching record -> revoked record;
        - source mismatch -> existing record unchanged.
        """
        self._validate_user_id(user_id)
        identifier = self._normalize_world_identifier(world_identifier)

        world = await asyncio.to_thread(
            self._learning_world_repository.get_by_identifier,
            identifier,
        )

        if world is None:
            raise LearningWorldNotFoundError(
                f"Learning World does not exist: {identifier}"
            )

        world_id = self._world_id(world)

        existing = await asyncio.to_thread(
            self._access_repository.get_by_user_and_world,
            user_id=user_id,
            world_id=world_id,
        )

        if existing is None:
            return None

        if (
            access_source is not None
            and existing.access_source != access_source
        ):
            return existing

        if not existing.is_active():
            return existing

        revoked = existing.revoke()

        return await asyncio.to_thread(
            self._access_repository.save,
            revoked,
        )
    async def has_access(
        self,
        *,
        user_id: UUID,
        world_identifier: str,
    ) -> bool:
        access = await self.get_access(
            user_id=user_id,
            world_identifier=world_identifier,
        )
        return access is not None and access.is_active()

    async def require_access(
        self,
        *,
        user_id: UUID,
        world_identifier: str,
    ) -> LearnerWorldAccess:
        access = await self.get_access(
            user_id=user_id,
            world_identifier=world_identifier,
        )

        if access is None or not access.is_active():
            raise PermissionError(
                "Learner does not have active access to this Learning World."
            )

        return access

    async def get_access(
        self,
        *,
        user_id: UUID,
        world_identifier: str,
    ) -> LearnerWorldAccess | None:
        self._validate_user_id(user_id)
        identifier = self._normalize_world_identifier(world_identifier)

        world = await asyncio.to_thread(
            self._learning_world_repository.get_by_identifier,
            identifier,
        )

        if world is None:
            return None

        world_id = self._world_id(world)

        return await asyncio.to_thread(
            self._access_repository.get_by_user_and_world,
            user_id=user_id,
            world_id=world_id,
        )

    async def list_world_access(
        self,
        *,
        user_id: UUID,
    ) -> tuple[LearnerWorldAccess, ...]:
        self._validate_user_id(user_id)

        return await asyncio.to_thread(
            self._access_repository.list_by_user,
            user_id=user_id,
        )

    @staticmethod
    def _world_id(world) -> UUID:
        world_id = getattr(world, "id", None)
        if not isinstance(world_id, UUID):
            raise WorldAccessError(
                "Learning World catalogue entry must expose the "
                "authoritative World UUID as 'id'."
            )
        return world_id

    @staticmethod
    def _validate_user_id(user_id: UUID) -> None:
        if not isinstance(user_id, UUID):
            raise ValueError("user_id must be a UUID.")

    @staticmethod
    def _normalize_world_identifier(world_identifier: str) -> str:
        if not isinstance(world_identifier, str):
            raise ValueError("world_identifier must be a string.")

        identifier = world_identifier.strip()

        if not identifier:
            raise ValueError("world_identifier is required.")

        if len(identifier) > 100:
            raise ValueError("world_identifier is too long.")

        return identifier


__all__ = [
    "CanonicalUserIdentityReader",
    "LearningWorldDisabledError",
    "LearningWorldNotFoundError",
    "UserNotFoundError",
    "WorldAccessError",
    "WorldAccessService",
]

