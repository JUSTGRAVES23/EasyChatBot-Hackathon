"""
Voice Call Orchestrator.

Coordinates the preparation of a voice call.

Responsibilities:
- Build interaction context.
- Create character voice session.
- Create domain voice call session.
- Apply voice call runtime lifecycle.

Does NOT:
- Execute AI providers.
- Manage LiveKit.
- Handle HTTP.
- Persist data.
"""

from __future__ import annotations


from dataclasses import dataclass


from backend.app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)


from backend.app.application.uai.context.interaction_context_builder import (
    InteractionContextBuilder,
)


from backend.app.application.uai.voice.voice_character_session_service import (
    VoiceCharacterSessionService,
)


from app.ai_runtime.voice.voice_call_runtime import (
    VoiceCallRuntime,
)


from app.domain.uai.context.learner_context import (
    LearnerContext,
)


from app.domain.uai.context.voice_context import (
    VoiceContext,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallOrchestrator:
    """
    Voice call workflow coordinator.
    """

    context_builder: InteractionContextBuilder

    session_service: VoiceCharacterSessionService

    voice_runtime: VoiceCallRuntime = (
        VoiceCallRuntime()
    )



    def prepare_call(
        self,
        *,
        request: VoiceCallRequest,
    ) -> VoiceCallSession:
        """
        Prepare voice call session.

        Flow:

        Request
          |
          â†“
        Interaction Context
          |
          â†“
        Character Voice Session
          |
          â†“
        Voice Call Session
          |
          â†“
        Runtime Preparation
          |
          â†“
        READY state
        """


        learner = LearnerContext(
            learner_id=request.learner_id,
            learning_goals=[
                "conversation",
            ],
        )


        voice = VoiceContext(
            language_code=request.language_code,
            voice_provider="openai",
            voice_profile="verse",
        )


        context = (
            self.context_builder
            .build(
                learner=learner,
                world_id=request.world_id,
                character_id=request.character_id,
                voice=voice,
            )
        )


        voice_session = (
            self.session_service
            .create_session(
                context=context,
            )
        )


        call_session = VoiceCallSession(
            session_id=(
                voice_session.session_id
            ),
            learner_id=request.learner_id,
            character_id=request.character_id,
            world_id=request.world_id,
            language_code=request.language_code,
        )


        return (
            self.voice_runtime
            .prepare(
                session=call_session,
            )
        )
