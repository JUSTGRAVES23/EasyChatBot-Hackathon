"""
Voice Call Application Service.

Application boundary for voice calls.

Responsibilities:
- Receive voice call requests.
- Delegate preparation workflow.
- Return prepared call information.

Does NOT:
- Execute speech.
- Manage providers.
- Manage HTTP.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)


from app.application.uai.voice.voice_call_orchestrator import (
    VoiceCallOrchestrator,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallService:
    """
    Voice call application service.
    """

    orchestrator: VoiceCallOrchestrator



    def prepare_call(
        self,
        *,
        request: VoiceCallRequest,
    ) -> dict:
        """
        Prepare voice call.
        """


        session = (
            self.orchestrator
            .prepare_call(
                request=request
            )
        )


        return {
            "room_name": (
                session.session_id
            ),
            "character_id": (
                session.character_id
            ),
            "language_code": (
                session.language_code
            ),
            "provider": (
                "livekit"
            ),
        }



