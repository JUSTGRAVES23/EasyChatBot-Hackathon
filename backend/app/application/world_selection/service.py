"""Authenticated World-selection application service.

This is a thin application seam over the existing authoritative services:
LearningWorldCatalogueService resolves the public catalogue identifier and
BetaAccessService.assign_world performs the existing authenticated persistence
and eligibility checks.

No World entitlement, Telegram, conversation, or AI/runtime side effects are
introduced here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class WorldCataloguePort(Protocol):
    def resolve_runtime_world(self, identifier: str): ...


class BetaAccessPort(Protocol):
    async def assign_world(self, *, user_id: str, world_id: str): ...


@dataclass(frozen=True, slots=True)
class WorldSelectionResult:
    world_id: str


class WorldSelectionService:
    def __init__(
        self,
        *,
        world_catalogue: WorldCataloguePort,
        beta_access: BetaAccessPort,
    ) -> None:
        self._world_catalogue = world_catalogue
        self._beta_access = beta_access

    async def assign_world(
        self,
        *,
        user_id: str,
        world_identifier: str,
    ) -> WorldSelectionResult:
        if not world_identifier:
            raise ValueError("world_id is required.")

        # Public/frontend World identity is resolved by the authoritative
        # catalogue. The resulting runtime ID is then passed to the existing
        # BetaAccessService, which remains authoritative for eligibility and
        # persistence.
        world = self._world_catalogue.resolve_runtime_world(world_identifier)
        selected = await self._beta_access.assign_world(
            user_id=user_id,
            world_id=world.world_id,
        )

        return WorldSelectionResult(world_id=selected.active_world_id or world.world_id)
