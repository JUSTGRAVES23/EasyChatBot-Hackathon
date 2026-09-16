"""
World Resolver.

Application service responsible for resolving a learner's
active World into validated runtime context.
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
    Repository contract for World retrieval.
    """

    def get_by_id(
        self,
        world_id: str,
    ):
        """
        Retrieve a World configuration.
        """
        ...


class WorldResolver:
    """
    Resolves a World configuration into runtime context.
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
        Resolve World configuration.
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
            world_type=world.world_type,
            learning_domain=world.learning_domain,
            language_policy=world.language_policy,
            available_characters=tuple(
                world.available_characters
            ),
        )