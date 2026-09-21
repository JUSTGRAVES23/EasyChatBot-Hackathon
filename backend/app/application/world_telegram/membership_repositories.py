"""Repository port for World Telegram learner memberships."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.world_telegram import WorldTelegramMembership


class WorldTelegramMembershipRepository(Protocol):
    """Persistence contract for World Telegram memberships."""

    def get_by_id(self, membership_id: UUID) -> WorldTelegramMembership | None:
        ...

    def get_by_destination_and_user(
        self,
        *,
        destination_id: UUID,
        user_id: UUID,
    ) -> WorldTelegramMembership | None:
        ...

    def list_by_destination(
        self,
        destination_id: UUID,
    ) -> tuple[WorldTelegramMembership, ...]:
        ...

    def save(
        self,
        membership: WorldTelegramMembership,
    ) -> WorldTelegramMembership:
        ...

    def delete(self, membership_id: UUID) -> bool:
        ...
