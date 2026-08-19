"""
Voice Call Execution Service.

Application service responsible for
controlling execution of prepared
voice calls.

Responsibilities:
- Coordinate voice execution runtime.
- Build execution context.
- Expose application-level actions.

Does NOT:
- Handle HTTP.
- Manage LiveKit.
- Execute speech providers directly.
- Persist data.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


from app.domain.uai.voice.voice_call_room import (
    VoiceCallRoom,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_participant import (
    VoiceCallParticipant,
    VoiceParticipantRole,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallExecutionService:
    """
    Application boundary for
    voice call execution.
    """

    execution_runtime: VoiceCallExecutionRuntime



    def _build_context(
        self,
        *,
        session: VoiceCallSession,
    ) -> VoiceCallExecutionContext:
        """
        Build runtime execution context.

        Beta composition:

        Learner
            +
        Character
        """


        learner = VoiceCallParticipant(
            participant_id=session.learner_id,
            role=VoiceParticipantRole.LEARNER,
            display_name="Learner",
        )


        character = VoiceCallParticipant(
            participant_id=session.character_id,
            role=VoiceParticipantRole.CHARACTER,
            display_name=session.character_id,
        )


        room = VoiceCallRoom(
            room_id=session.session_id,
            participants=(
                learner,
                character,
            ),
        )


        return VoiceCallExecutionContext(
            session=session,
            room=room,
        )



    def start_call(
        self,
        *,
        session: VoiceCallSession,
    ) -> VoiceCallSession:
        """
        Start voice call execution.
        """


        context = self._build_context(
            session=session,
        )


        return (
            self.execution_runtime
            .start(
                context=context,
            )
        )



    def stop_call(
        self,
        *,
        session: VoiceCallSession,
    ) -> VoiceCallSession:
        """
        Stop voice call execution.
        """


        context = self._build_context(
            session=session,
        )


        return (
            self.execution_runtime
            .stop(
                context=context,
            )
        )



    def fail_call(
        self,
        *,
        session: VoiceCallSession,
    ) -> VoiceCallSession:
        """
        Mark voice call execution failed.
        """


        context = self._build_context(
            session=session,
        )


        return (
            self.execution_runtime
            .fail(
                context=context,
            )
        )