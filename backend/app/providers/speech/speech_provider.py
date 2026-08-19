"""
Speech Provider Contract.

Defines the abstraction for speech services.

Supported capabilities:
- Speech to Text (STT)
- Text to Speech (TTS)

The AI Runtime depends on this contract,
not on a specific vendor.

Possible implementations:
- OpenAI Speech
- ElevenLabs
- Azure Speech
- Local models

Does NOT:
- Manage conversations.
- Manage characters.
- Manage LiveKit rooms.
- Store user data.
"""

from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)



class SpeechProvider(
    ABC
):
    """
    Abstract speech provider.

    Provider implementations must
    implement this interface.
    """


    @abstractmethod
    def transcribe(
        self,
        audio: bytes,
        language_code: str,
    ) -> str:
        """
        Convert audio into text.

        Parameters
        ----------
        audio:
            Raw audio bytes.

        language_code:
            Expected language.

        Returns
        -------
        str
            Transcribed text.
        """

        raise NotImplementedError



    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_profile: str,
        language_code: str,
    ) -> bytes:
        """
        Convert text into audio.

        Parameters
        ----------
        text:
            Text to speak.

        voice_profile:
            Character voice profile.

        language_code:
            Output language.

        Returns
        -------
        bytes
            Generated audio.
        """

        raise NotImplementedError