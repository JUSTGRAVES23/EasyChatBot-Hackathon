"""
Voice Connection Token Domain Model.

Represents connection credentials
required to join a voice session.

Does NOT:
- Generate tokens.
- Call LiveKit.
- Manage providers.
- Handle authentication.
- Persist data.

It only represents validated
voice connection state.
"""

from __future__ import annotations


from dataclasses import dataclass


from datetime import datetime



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceConnectionToken:
    """
    Immutable voice connection token.

    Represents provider-independent
    connection credentials.
    """

    token: str

    room_name: str

    provider: str

    expires_at: datetime



    def __post_init__(self) -> None:
        """
        Validate token state.
        """


        if not self.token.strip():
            raise ValueError(
                "token cannot be empty."
            )


        if not self.room_name.strip():
            raise ValueError(
                "room_name cannot be empty."
            )


        if not self.provider.strip():
            raise ValueError(
                "provider cannot be empty."
            )


        if self.expires_at <= datetime.utcnow():
            raise ValueError(
                "expires_at must be in the future."
            )



__all__ = [
    "VoiceConnectionToken",
]