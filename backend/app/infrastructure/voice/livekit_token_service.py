"""
LiveKit Token Service.

Infrastructure service responsible for
creating voice connection credentials.

Responsibilities:
- Generate provider-specific tokens.
- Hide LiveKit implementation details.
- Return provider-independent domain model.

Does NOT:
- Handle HTTP.
- Manage application workflows.
- Decide authorization rules.
- Persist tokens.
- Execute voice calls.
"""

from __future__ import annotations


from datetime import datetime, timedelta


import uuid


from app.domain.uai.voice.voice_connection_token import (
    VoiceConnectionToken,
)



class LiveKitTokenService:
    """
    Infrastructure adapter for LiveKit tokens.

    Beta 1 implementation:
    - Generates deterministic provider abstraction.
    - Real LiveKit SDK integration can replace
      this implementation later.
    """



    def create_token(
        self,
        *,
        room_name: str,
        expires_minutes: int = 30,
    ) -> VoiceConnectionToken:
        """
        Create a voice connection token.

        Parameters
        ----------
        room_name:
            Voice room identifier.

        expires_minutes:
            Token validity period.

        Returns
        -------
        VoiceConnectionToken
            Provider-independent token model.
        """


        if not room_name.strip():
            raise ValueError(
                "room_name cannot be empty."
            )


        if expires_minutes <= 0:
            raise ValueError(
                "expires_minutes must be positive."
            )


        token = (
            f"livekit-{uuid.uuid4()}"
        )


        expires_at = (
            datetime.utcnow()
            + timedelta(
                minutes=expires_minutes,
            )
        )


        return VoiceConnectionToken(
            token=token,
            room_name=room_name,
            provider="livekit",
            expires_at=expires_at,
        )



__all__ = [
    "LiveKitTokenService",
]