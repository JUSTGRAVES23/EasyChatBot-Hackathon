"""
OpenAI Speech Provider Adapter.

Adapter between the generic
SpeechProvider contract and OpenAI services.

Responsibilities:
- Implement SpeechProvider interface.
- Translate runtime requests.

Does NOT:
- Manage conversations.
- Manage characters.
- Create voice rooms.
- Store user data.

Future:
- Replace internal implementation
  with OpenAI SDK calls.
"""

from __future__ import annotations


from app.providers.speech.speech_provider import (
    SpeechProvider,
)



class OpenAISpeechProvider(
    SpeechProvider
):
    """
    OpenAI speech adapter.

    Provider implementation remains
    behind the SpeechProvider contract.
    """



    def transcribe(
        self,
        audio: bytes,
        language_code: str,
    ) -> str:
        """
        Convert audio to text.

        Placeholder implementation.

        Real implementation will:
        - call OpenAI speech-to-text
        - handle provider errors
        - apply observability
        """

        raise NotImplementedError(
            "OpenAI transcription not implemented yet."
        )



    def synthesize(
        self,
        text: str,
        voice_profile: str,
        language_code: str,
    ) -> bytes:
        """
        Convert text to speech.

        Placeholder implementation.

        Real implementation will:
        - call OpenAI TTS
        - return audio stream
        """

        raise NotImplementedError(
            "OpenAI synthesis not implemented yet."
        )