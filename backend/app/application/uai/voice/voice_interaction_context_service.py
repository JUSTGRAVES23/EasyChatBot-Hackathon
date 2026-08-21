"""
Voice Interaction Context Service.

Application service responsible for translating
a voice call execution context into the existing
UAI InteractionContext.

Responsibilities:
- Build LearnerContext from the voice call session.
- Build VoiceContext from the voice call session.
- Delegate world and character resolution to
  InteractionContextBuilder.
- Return the established InteractionContext contract.

Does NOT:
- Handle HTTP.
- Connect to LiveKit.
- Execute AI agents.
- Manage LiveKit sessions.
- Persist data.
- Resolve worlds or characters directly.
"""

from __future__ import annotations


from dataclasses import dataclass


from backend.app.application.uai.context.interaction_context_builder import (
    InteractionContextBuilder,
)


from app.domain.uai.context.interaction_context import (
    InteractionContext,
)


from app.domain.uai.context.learner_context import (
    LearnerContext,
)


from app.domain.uai.context.voice_context import (
    VoiceContext,
)


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceInteractionContextService:
    """
    Application boundary for creating the established
    UAI InteractionContext from a voice call context.
    """

    context_builder: InteractionContextBuilder



    def build(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> InteractionContext:
        """
        Build InteractionContext for a voice call.
        """

        session = context.session


        learner = LearnerContext(
            learner_id=session.learner_id,
        )


        voice = VoiceContext(
            language_code=session.language_code,
            voice_provider="openai",
            voice_profile=session.character_id,
        )


        return (
            self.context_builder
            .build(
                learner=learner,
                world_id=session.world_id,
                character_id=session.character_id,
                voice=voice,
            )
        )



__all__ = [
    "VoiceInteractionContextService",
]
