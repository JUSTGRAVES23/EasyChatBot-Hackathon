"""
Voice Call Runtime.

Runtime orchestration layer for
AI character voice calls.

Responsibilities:
- Manage voice call lifecycle execution.
- Coordinate voice session activation.
- Apply runtime boundaries.
- Return runtime state changes.

Does NOT:
- Handle HTTP requests.
- Create API responses.
- Manage persistence.
- Select providers.
- Directly manage LiveKit.
"""

from __future__ import annotations


from dataclasses import dataclass


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
class VoiceCallRuntime:
    """
    Runtime coordinator for voice calls.
    """



    def prepare(
        self,
        *,
        session: VoiceCallSession,
    ) -> VoiceCallSession:
        """
        Prepare a voice call for activation.

        Transition:

        CREATED
            |
            ↓
        PREPARING
            |
            ↓
        READY
        """


        if session.state not in {
            VoiceCallState.CREATED,
            VoiceCallState.PREPARING,
        }:
            raise ValueError(
                "Voice call cannot be prepared "
                f"from state {session.state.value}."
            )


        return VoiceCallSession(
            session_id=session.session_id,
            learner_id=session.learner_id,
            character_id=session.character_id,
            world_id=session.world_id,
            language_code=session.language_code,
            state=VoiceCallState.READY,
        )



    def activate(
        self,
        *,
        session: VoiceCallSession,
    ) -> VoiceCallSession:
        """
        Activate a prepared voice call.

        Transition:

        READY
          |
          ↓
        ACTIVE
        """


        if session.state != (
            VoiceCallState.READY
        ):
            raise ValueError(
                "Voice call must be ready "
                "before activation."
            )


        return VoiceCallSession(
            session_id=session.session_id,
            learner_id=session.learner_id,
            character_id=session.character_id,
            world_id=session.world_id,
            language_code=session.language_code,
            state=VoiceCallState.ACTIVE,
        )



    def end(
        self,
        *,
        session: VoiceCallSession,
    ) -> VoiceCallSession:
        """
        End an active voice call.

        Transition:

        ACTIVE
          |
          ↓
        ENDED
        """


        if session.state != (
            VoiceCallState.ACTIVE
        ):
            raise ValueError(
                "Only active calls can be ended."
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
        session: VoiceCallSession,
    ) -> VoiceCallSession:
        """
        Mark voice call as failed.
        """


        return VoiceCallSession(
            session_id=session.session_id,
            learner_id=session.learner_id,
            character_id=session.character_id,
            world_id=session.world_id,
            language_code=session.language_code,
            state=VoiceCallState.FAILED,
        )