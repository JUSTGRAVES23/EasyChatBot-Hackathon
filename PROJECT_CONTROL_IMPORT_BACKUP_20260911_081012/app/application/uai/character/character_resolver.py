"""
Character Resolver.

Application service responsible for converting
character profile configuration into runtime
character context.

Responsibilities:
- Resolve character profiles.
- Extract interaction-level character data.
- Create CharacterContext.

Does not:
- Load files directly.
- Manage AI providers.
- Create voice sessions.
- Manage subscriptions.
"""

from __future__ import annotations

import logging

from app.domain.uai.context.character_context import (
    CharacterContext,
)


logger = logging.getLogger(__name__)


class CharacterResolver:
    """
    Resolves character runtime context.
    """

    def __init__(
        self,
        *,
        character_repository,
    ) -> None:
        """
        Initialise resolver.

        Parameters
        ----------
        character_repository:
            Repository providing character profiles.
        """

        self._character_repository = (
            character_repository
        )


    def resolve(
        self,
        character_id: str,
    ) -> CharacterContext:
        """
        Resolve character configuration.

        Parameters
        ----------
        character_id:
            Character identifier.

        Returns
        -------
        CharacterContext

        Raises
        ------
        ValueError
            If character does not exist.
        """

        logger.info(
            "Resolving character context",
            extra={
                "character_id": character_id,
            },
        )


        character = (
            self._character_repository
            .get_by_id(character_id)
        )


        if character is None:
            raise ValueError(
                f"Character not found: {character_id}"
            )


        identity = (
            character.get(
                "identity",
                {},
            )
        )


        behaviour = (
            character.get(
                "behaviour",
                {},
            )
        )


        context = CharacterContext(
            character_id=(
                character["id"]
            ),

            name=(
                character["name"]
            ),

            personality_reference=(
                identity.get(
                    "role",
                    "default",
                )
            ),

            teaching_style=(
                identity.get(
                    "communication_style",
                    "default",
                )
            ),

            premium_required=(
                character.get(
                    "premium_required",
                    False,
                )
            ),
        )


        logger.info(
            "Character context resolved",
            extra={
                "character_id": character_id,
            },
        )


        return context
