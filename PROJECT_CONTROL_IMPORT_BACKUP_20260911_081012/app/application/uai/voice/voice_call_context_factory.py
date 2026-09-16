"""
Voice Call Context Factory.

Application factory responsible for
creating voice execution contexts.

Responsibilities:
- Convert voice call requests into
  domain execution context.
- Create voice sessions.
- Create room participants.
- Build validated execution boundary.
- Preserve an existing persistent
  VoiceCall identity when supplied.

Does NOT:
- Handle HTTP.
- Execute runtime.
- Connect LiveKit.
- Select providers.
- Persist data.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)

from app.domain.uai.voice.voice_call import (
    VoiceCall,
)

from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)

from app.domain.uai.voice.voice_call_participant import (
    VoiceCallParticipant,
    VoiceParticipantRole,
)

from app.domain.uai.voice.voice_call_room import (
    VoiceCallRoom,
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
class VoiceCallContextFactory:
    """
    Creates voice execution contexts.

    The factory does not create or persist
    VoiceCall aggregates.

    It supports both:
    - request-based context creation
    - context creation from an existing
      authoritative VoiceCallSession.
    """

    def create(
        self,
        *,
        request: VoiceCallRequest,
        voice_call: VoiceCall | None = None,
    ) -> VoiceCallExecutionContext:
        """
        Create an execution context from a
        voice call request.

        When ``voice_call`` is supplied, the
        persistent VoiceCall identity is preserved
        in the execution context.
        """

        session = VoiceCallSession(
            session_id=(
                f"{request.character_id}-"
                f"{request.learner_id}"
            ),
            learner_id=request.learner_id,
            character_id=request.character_id,
            world_id=request.world_id,
            language_code=request.language_code,
            state=VoiceCallState.READY,
        )

        return self.create_from_session(
            session=session,
            voice_call=voice_call,
        )

    def create_from_session(
        self,
        *,
        session: VoiceCallSession,
        voice_call: VoiceCall,
    ) -> VoiceCallExecutionContext:
        """
        Create an execution context around an
        existing authoritative voice session.

        The supplied session is reused unchanged.
        No second session is created.
        """

        room = VoiceCallRoom(
            room_id=session.session_id,
            participants=(
                VoiceCallParticipant(
                    participant_id=session.learner_id,
                    role=VoiceParticipantRole.LEARNER,
                    display_name="Learner",
                ),
                VoiceCallParticipant(
                    participant_id=session.character_id,
                    role=VoiceParticipantRole.CHARACTER,
                    display_name=session.character_id,
                ),
            ),
        )

        return VoiceCallExecutionContext(
            session=session,
            room=room,
            voice_call=voice_call,
        )


__all__ = [
    "VoiceCallContextFactory",
]

