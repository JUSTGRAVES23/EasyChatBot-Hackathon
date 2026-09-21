"""Beta policy for provisioning access to the complete World catalogue."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.domain.learning.learner_world_access import BETA, LearnerWorldAccess


class BetaUserReadBoundary(Protocol):
    async def get_beta_user(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        """Return the controlled Beta-user DTO or None."""
        ...


class CanonicalUserIdentityReader(Protocol):
    async def get_user_for_identity(
        self,
        user_id: UUID,
    ):
        """Return the canonical user record or None."""
        ...


class WorldCatalogueBoundary(Protocol):
    def list_all(self):
        """Return all configured catalogue Worlds."""
        ...


class WorldAccessBoundary(Protocol):
    async def grant_access(
        self,
        *,
        user_id: UUID,
        world_identifier: str,
        access_source: str = BETA,
        allow_disabled_world: bool = False,
    ) -> LearnerWorldAccess:
        ...


class BetaWorldAccessError(ValueError):
    """Expected Beta World-access provisioning failure."""


class BetaUserNotFoundError(BetaWorldAccessError):
    """The requested Beta user does not exist."""


class BetaUserNotEligibleError(BetaWorldAccessError):
    """The Beta user is not verified and approved."""


class CanonicalUserNotFoundError(BetaWorldAccessError):
    """The Beta user cannot be resolved through canonical identity."""


class BetaWorldAccessService:
    """
    Provision durable Beta access for every World in the authoritative catalogue.

    Policy:
        verified + Beta-approved learner
            -> all catalogue Worlds

    ``enabled`` is intentionally NOT filtered here. The service uses the
    explicit WorldAccessService provisioning flag so disabled Worlds can
    receive durable portfolio access. Runtime/Study Mode entry must still
    enforce current World availability.
    """

    def __init__(
        self,
        *,
        beta_user_reader: BetaUserReadBoundary,
        user_identity_reader: CanonicalUserIdentityReader,
        world_catalogue: WorldCatalogueBoundary,
        world_access: WorldAccessBoundary,
    ) -> None:
        if beta_user_reader is None:
            raise ValueError("beta_user_reader is required.")
        if user_identity_reader is None:
            raise ValueError("user_identity_reader is required.")
        if world_catalogue is None:
            raise ValueError("world_catalogue is required.")
        if world_access is None:
            raise ValueError("world_access is required.")

        self._beta_user_reader = beta_user_reader
        self._user_identity_reader = user_identity_reader
        self._world_catalogue = world_catalogue
        self._world_access = world_access

    async def provision_all_worlds(
        self,
        *,
        beta_user_id: str,
    ) -> tuple[LearnerWorldAccess, ...]:
        if not isinstance(beta_user_id, str) or not beta_user_id.strip():
            raise ValueError("beta_user_id is required.")

        beta_user = await self._beta_user_reader.get_beta_user(
            beta_user_id.strip()
        )

        if beta_user is None:
            raise BetaUserNotFoundError(
                "Beta user does not exist."
            )

        if not bool(beta_user.get("email_verified")):
            raise BetaUserNotEligibleError(
                "Email must be verified before World access provisioning."
            )

        if not bool(beta_user.get("beta_approved")):
            raise BetaUserNotEligibleError(
                "User is not Beta approved."
            )

        canonical_user_id = self._canonical_uuid(
            beta_user.get("user_id")
        )

        canonical_user = await self._user_identity_reader.get_user_for_identity(
            canonical_user_id
        )

        if canonical_user is None:
            raise CanonicalUserNotFoundError(
                "Canonical user does not exist."
            )

        worlds = tuple(self._world_catalogue.list_all())

        # The authoritative catalogue is the only source of World scope.
        # There is deliberately no language/World allow-list here.
        granted: list[LearnerWorldAccess] = []

        for world in worlds:
            identifier = getattr(world, "identifier", None)

            if not isinstance(identifier, str) or not identifier.strip():
                raise BetaWorldAccessError(
                    "Authoritative World catalogue contains an invalid identifier."
                )

            access = await self._world_access.grant_access(
                user_id=canonical_user_id,
                world_identifier=identifier.strip(),
                access_source=BETA,
                allow_disabled_world=True,
            )
            granted.append(access)

        return tuple(granted)

    @staticmethod
    def _canonical_uuid(value: Any) -> UUID:
        if isinstance(value, UUID):
            return value

        if not isinstance(value, str) or not value.strip():
            raise BetaWorldAccessError(
                "Beta user must expose a canonical UUID user_id."
            )

        try:
            return UUID(value.strip())
        except ValueError as exc:
            raise BetaWorldAccessError(
                "Beta user user_id is not a valid canonical UUID."
            ) from exc


__all__ = [
    "BetaUserNotEligibleError",
    "BetaUserNotFoundError",
    "BetaWorldAccessError",
    "BetaWorldAccessService",
    "CanonicalUserNotFoundError",
]
