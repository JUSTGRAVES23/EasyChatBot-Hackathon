"""
Voice Context.

Represents voice configuration required
for an AI interaction.

Does not execute:
- STT
- TTS
- LiveKit

It only carries configuration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class VoiceContext:
    """
    Immutable voice context.
    """

    language_code: str

    voice_provider: str

    voice_profile: str

    enabled: bool = True

    def __post_init__(self) -> None:
        """
        Validate voice context.
        """

        if not self.language_code.strip():
            raise ValueError(
                "language_code cannot be empty."
            )

        if not self.voice_provider.strip():
            raise ValueError(
                "voice_provider cannot be empty."
            )

        if not self.voice_profile.strip():
            raise ValueError(
                "voice_profile cannot be empty."
            )