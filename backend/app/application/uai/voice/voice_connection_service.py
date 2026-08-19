"""
Voice Connection Service.

Application service responsible for
creating voice connection credentials.

Responsibilities:
- Coordinate token creation.
- Request infrastructure token generation.
- Return domain connection token.

Does NOT:
- Handle HTTP.
- Generate provider tokens.
- Manage LiveKit directly.
- Persist credentials.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.infrastructure.voice.livekit_token_service import (
    LiveKitTokenService,
)


from app.domain.uai.voice.voice_connection_token import (
    VoiceConnectionToken,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceConnectionService:
    """
    Application boundary for voice connections.
    """

    token_service: LiveKitTokenService



    def create_connection(
        self,
        *,
        room_name: str,
    ) -> VoiceConnectionToken:
        """
        Create voice connection credentials.
        """


        return (
            self.token_service
            .create_token(
                room_name=room_name,
            )
        )



__all__ = [
    "VoiceConnectionService",
]