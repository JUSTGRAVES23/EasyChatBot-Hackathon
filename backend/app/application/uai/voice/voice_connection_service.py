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

from app.application.uai.voice.voice_connection_port import (
    VoiceConnectionPort,
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

    token_service: VoiceConnectionPort

    def create_connection(
        self,
        *,
        room_name: str,
        identity: str | None = None,
        expires_minutes: int = 30,
    ) -> VoiceConnectionToken:
        """
        Create voice connection credentials.

        Provider-specific token generation is delegated
        through VoiceConnectionPort.
        """

        if not room_name.strip():
            raise ValueError(
                "room_name cannot be empty."
            )

        if expires_minutes <= 0:
            raise ValueError(
                "expires_minutes must be positive."
            )

        if identity is not None and not identity.strip():
            raise ValueError(
                "identity cannot be empty."
            )

        return (
            self.token_service
            .create_connection_token(
                room_name=room_name,
                identity=identity,
                expires_minutes=expires_minutes,
            )
        )


__all__ = [
    "VoiceConnectionService",
]

