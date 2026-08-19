"""
Interaction Context Builder.

Application service responsible for composing
the complete UAI interaction context.

Responsibilities:
- Combine domain contexts.
- Coordinate runtime preparation.
- Create InteractionContext.

Does NOT:
- Call AI providers.
- Create LiveKit sessions.
- Persist memory.
- Execute agents.
"""

from __future__ import annotations

import logging

from app.domain.uai.context.interaction_context import (
    InteractionContext,
)

from app.domain.uai.context.learner_context import (
    LearnerContext,
)

from app.domain.uai.context.voice_context import (
    VoiceContext,
)

from app.domain.uai.context.world_context import (
    WorldContext,
)


from app.application.uai.character.character_resolver import (
    CharacterResolver,
)

from app.application.uai.world.world_resolver import (
    WorldResolver,
)


logger = logging.getLogger(__name__)


class InteractionContextBuilder:
    """
    Builds the complete UAI interaction context.
    """

    def __init__(
        self,
        *,
        world_resolver: WorldResolver,
        character_resolver: CharacterResolver,
    ) -> None:

        self._world_resolver = (
            world_resolver
        )

        self._character_resolver = (
            character_resolver
        )


    def build(
        self,
        *,
        learner: LearnerContext,
        world_id: str,
        character_id: str,
        voice: VoiceContext,
    ) -> InteractionContext:
        """
        Build interaction context.
        """

        logger.info(
            "Building interaction context",
            extra={
                "world_id": world_id,
                "character_id": character_id,
            },
        )


        world = (
            self._world_resolver
            .resolve(world_id)
        )


        character = (
            self._character_resolver
            .resolve(character_id)
        )


        context = InteractionContext(
            learner=learner,
            world=world,
            character=character,
            voice=voice,
        )


        logger.info(
            "Interaction context created",
        )


        return context