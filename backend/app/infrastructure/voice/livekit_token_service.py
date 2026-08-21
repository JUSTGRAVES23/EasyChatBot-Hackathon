"""
LiveKit Token Service.

Infrastructure service responsible for generating
real LiveKit participant access tokens.

Responsibilities:
- Generate signed LiveKit JWT access tokens.
- Grant participant access to a specific room.
- Keep LiveKit credentials inside infrastructure.
- Return provider-independent VoiceConnectionToken.

Does NOT:
- Handle HTTP.
- Manage application workflows.
- Decide business authorization.
- Persist tokens.
- Execute AI agents.
"""

from __future__ import annotations


from datetime import (
    datetime,
    timedelta,
    timezone,
)


import os
import uuid


from dotenv import load_dotenv


from livekit import api


from app.domain.uai.voice.voice_connection_token import (
    VoiceConnectionToken,
)


load_dotenv()



class LiveKitTokenService:
    """
    Real LiveKit access-token infrastructure adapter.
    """



    def create_token(
        self,
        *,
        room_name: str,
        identity: str | None = None,
        expires_minutes: int = 30,
    ) -> VoiceConnectionToken:
        """
        Create a signed LiveKit participant token.

        Parameters
        ----------
        room_name:
            LiveKit room the participant may join.

        identity:
            Unique LiveKit participant identity.

        expires_minutes:
            Token validity period.
        """



        if not room_name.strip():

            raise ValueError(
                "room_name cannot be empty."
            )



        if expires_minutes <= 0:

            raise ValueError(
                "expires_minutes must be positive."
            )



        participant_identity = (
            identity.strip()
            if identity is not None
            else f"learner-{uuid.uuid4()}"
        )



        if not participant_identity:

            raise ValueError(
                "identity cannot be empty."
            )



        api_key = os.getenv(
            "LIVEKIT_API_KEY"
        )



        api_secret = os.getenv(
            "LIVEKIT_API_SECRET"
        )



        if not api_key:

            raise RuntimeError(
                "LIVEKIT_API_KEY is not configured."
            )



        if not api_secret:

            raise RuntimeError(
                "LIVEKIT_API_SECRET is not configured."
            )



        expires_at = (
            datetime.now(
                timezone.utc
            )
            + timedelta(
                minutes=expires_minutes,
            )
        )



        access_token = (
            api.AccessToken(
                api_key=api_key,
                api_secret=api_secret,
            )
            .with_identity(
                participant_identity,
            )
            .with_name(
                participant_identity,
            )
            .with_ttl(
                timedelta(
                    minutes=expires_minutes,
                )
            )
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True,
                )
            )
        )



        token = (
            access_token.to_jwt()
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