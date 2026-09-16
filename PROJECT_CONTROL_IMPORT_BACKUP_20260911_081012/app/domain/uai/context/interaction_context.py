"""
UAI Interaction Context.

Represents the complete context of one AI interaction.

This object is a domain contract between:

- User interaction layer
- AI Runtime
- Character Runtime
- Voice Runtime

Responsibilities
----------------
- Hold validated interaction state.
- Provide immutable runtime context.
- Ensure all required context exists.

Does NOT
--------
- Call AI providers.
- Create conversations.
- Manage LiveKit.
- Persist data.
- Execute agents.

Architecture
------------

Learner Context
        +
World Context
        +
Character Context
        +
Voice Context

        |

        v

InteractionContext

        |

        v

AI Runtime


Design principles
-----------------
- Immutable
- Explicit dependencies
- Provider independent
- Easy to test
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.uai.context.character_context import (
    CharacterContext,
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


@dataclass(
    frozen=True,
    slots=True,
)
class InteractionContext:
    """
    Complete context required for an AI interaction.
    """

    learner: LearnerContext

    world: WorldContext

    character: CharacterContext

    voice: VoiceContext


    def __post_init__(self) -> None:
        """
        Validate mandatory contexts.
        """

        if self.learner is None:
            raise ValueError(
                "Learner context is required."
            )

        if self.world is None:
            raise ValueError(
                "World context is required."
            )

        if self.character is None:
            raise ValueError(
                "Character context is required."
            )

        if self.voice is None:
            raise ValueError(
                "Voice context is required."
            )
