"""
Voice Call Lifecycle Service.

Application facade for the complete
voice call lifecycle.

Responsibilities:
- Coordinate voice call execution.
- Create persistent voice call identity.
- Create execution sessions.
- Generate voice connections.
- Expose lifecycle operations.

Does NOT:
- Handle HTTP.
- Manage providers directly.
- Connect LiveKit directly.
- Persist directly.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.application.uai.voice.voice_call_execution_coordinator import (
    VoiceCallExecutionCoordinator,
)


from app.application.uai.voice.voice_connection_service import (
    VoiceConnectionService,
)


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


from app.domain.uai.voice.voice_call import (
    VoiceCall,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallLifecycleService:
    """
    Application lifecycle facade.

    Coordinates:

        VoiceCall
            |
            ↓
        VoiceCallSession
            |
            ↓
        Runtime Execution
            |
            ↓
        Connection
    """


    execution_coordinator: VoiceCallExecutionCoordinator

    connection_service: VoiceConnectionService | None = None

    voice_call_management_service: (
        VoiceCallManagementService | None
    ) = None

    voice_call_session_service: (
        VoiceCallSessionService | None
    ) = None



    def start_call(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> dict:
        """
        Prepare room, execute call,
        and create connection.
        """


        result = (
            self.execution_coordinator
            .start(
                context=context,
            )
        )


        if self.connection_service is not None:

            connection = (
                self.connection_service
                .create_connection(
                    room_name=(
                        result["room"]["room_name"]
                    ),
                )
            )


            result["connection"] = (
                connection
            )


        return result



    def create_voice_call(
        self,
        *,
        learner_id: str,
        character_id: str,
        world_id: str,
        language_code: str,
    ) -> VoiceCall:
        """
        Create persistent voice identity.
        """


        if (
            self.voice_call_management_service
            is None
        ):
            raise RuntimeError(
                "Voice call management service "
                "not configured."
            )


        return (
            self.voice_call_management_service
            .create_call(
                learner_id=learner_id,
                character_id=character_id,
                world_id=world_id,
                language_code=language_code,
            )
        )



    def create_session(
        self,
        *,
        voice_call: VoiceCall,
    ) -> VoiceCallSession:
        """
        Create execution session.
        """


        if (
            self.voice_call_session_service
            is None
        ):
            raise RuntimeError(
                "Voice call session service "
                "not configured."
            )


        return (
            self.voice_call_session_service
            .create_session(
                voice_call=voice_call,
            )
        )



    def reconnect_call(
        self,
        *,
        voice_call: VoiceCall,
    ) -> VoiceCallSession:
        """
        Reconnect existing voice call.
        """


        if (
            self.voice_call_session_service
            is None
        ):
            raise RuntimeError(
                "Voice call session service "
                "not configured."
            )


        return (
            self.voice_call_session_service
            .reconnect_session(
                voice_call=voice_call,
            )
        )



__all__ = [
    "VoiceCallLifecycleService",
]