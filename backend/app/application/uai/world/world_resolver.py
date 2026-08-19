"""
World Resolver.

Application service responsible for resolving
the learner's active AI learning world.

Responsibilities
----------------

- Retrieve world configuration.
- Validate world availability.
- Create WorldContext.

Does NOT
--------

- Execute AI models.
- Manage characters.
- Create conversations.
- Handle persistence directly.
"""

from __future__ import annotations

import logging
from typing import Protocol

from app.domain.uai.context.world_context import (
    WorldContext,
)


logger = logging.getLogger(__name__)


class WorldRepository(Protocol):
    """
    Repository contract for world retrieval.
    """

    def get_by_id(
        self,
        world_id: str,
    ):
        """
        Retrieve a world configuration.
        """
        ...


class WorldResolver:
    """
    Resolves a learning world into runtime context.
    """

    def __init__(
        self,
        *,
        world_repository: WorldRepository,
    ) -> None:
        self._world_repository = world_repository

    def resolve(
        self,
        world_id: str,
    ) -> WorldContext:
        """
        Resolve world configuration.

        Returns
        -------
        WorldContext
            Validated world interaction context.
        """

        logger.info(
            "Resolving world context",
            extra={
                "world_id": world_id,
            },
        )

        world = (
            self._world_repository
            .get_by_id(world_id)
        )

        if world is None:
            raise ValueError(
                f"World not found: {world_id}"
            )

        return WorldContext(
            world_id=world.id,
            name=world.name,
            language_code=world.language_code,
            available_characters=(
                tuple(
                    world.available_characters
                )
            ),
        )