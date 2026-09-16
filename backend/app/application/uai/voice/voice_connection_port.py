"""
Voice Connection Port.

Application-owned abstraction for voice connection
credential generation.

The application layer depends on this contract,
not on a concrete provider implementation.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.uai.voice.voice_connection_token import (
    VoiceConnectionToken,
)


class VoiceConnectionPort(Protocol):
    """
    Application-facing contract for voice connection
    credential generation.

    Infrastructure adapters implement this contract
    through Python structural typing.
    """

    def create_connection_token(
        self,
        *,
        room_name: str,
        identity: str | None = None,
        expires_minutes: int = 30,
    ) -> VoiceConnectionToken:
        """
        Create provider-independent voice connection credentials.
        """
        ...


__all__ = [
    "VoiceConnectionPort",
]

