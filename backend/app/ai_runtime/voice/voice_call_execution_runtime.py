"""
Voice Call Execution Runtime.

Runtime execution coordinator for
AI character voice calls.

Responsibilities:
- Execute prepared voice call sessions.
- Coordinate execution lifecycle.
- Validate execution context.
- Provide runtime boundaries.

Does NOT:
- Handle HTTP.
- Persist sessions.
- Manage authentication.
- Own LiveKit connections.
- Select providers.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallExecutionRuntime:
    """
    Executes prepared voice calls.
    """



    def start(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> VoiceCallSession:
        """
        Start voice call execution.

        Expected lifecycle:

        READY
          |
          ↓
        ACTIVE
        """


        session = (
            context.session
        )


        if session.state != (
            VoiceCallState.READY
        ):
            raise ValueError(
                "Voice call must be READY "
                "before execution."
            )


        if not context.room.has_character():

            raise ValueError(
                "Voice call room requires "
                "a character participant."
            )


        return VoiceCallSession(
            session_id=session.session_id,
            learner_id=session.learner_id,
            character_id=session.character_id,
            world_id=session.world_id,
            language_code=session.language_code,
            state=VoiceCallState.ACTIVE,
        )



    def stop(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> VoiceCallSession:
        """
        Stop voice call execution.

        Expected lifecycle:

        ACTIVE
          |
          ↓
        ENDED
        """


        session = (
            context.session
        )


        if session.state != (
            VoiceCallState.ACTIVE
        ):
            raise ValueError(
                "Only ACTIVE voice calls "
                "can be stopped."
            )


        return VoiceCallSession(
            session_id=session.session_id,
            learner_id=session.learner_id,
            character_id=session.character_id,
            world_id=session.world_id,
            language_code=session.language_code,
            state=VoiceCallState.ENDED,
        )



    def fail(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> VoiceCallSession:
        """
        Mark execution as failed.
        """


        session = (
            context.session
        )


        return VoiceCallSession(
            session_id=session.session_id,
            learner_id=session.learner_id,
            character_id=session.character_id,
            world_id=session.world_id,
            language_code=session.language_code,
            state=VoiceCallState.FAILED,
        )