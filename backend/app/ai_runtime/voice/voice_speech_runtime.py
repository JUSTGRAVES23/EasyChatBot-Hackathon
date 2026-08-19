"""
Voice Speech Runtime.

Runtime bridge between AI characters
and speech providers.

Responsibilities:
- Coordinate speech generation.
- Use provider abstraction.
- Keep AI runtime provider independent.

Does NOT:
- Call vendors directly.
- Manage LiveKit rooms.
- Store secrets.
- Manage conversations.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.providers.speech.speech_provider import (
    SpeechProvider,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceSpeechRuntime:
    """
    Runtime service for speech operations.

    Depends on the SpeechProvider abstraction.
    """

    speech_provider: SpeechProvider



    def transcribe(
        self,
        *,
        audio: bytes,
        language_code: str,
    ) -> str:
        """
        Convert audio input into text.
        """

        return self.speech_provider.transcribe(
            audio=audio,
            language_code=language_code,
        )



    def synthesize(
        self,
        *,
        text: str,
        voice_profile: str,
        language_code: str,
    ) -> bytes:
        """
        Convert text into generated audio.
        """

        return self.speech_provider.synthesize(
            text=text,
            voice_profile=voice_profile,
            language_code=language_code,
        )