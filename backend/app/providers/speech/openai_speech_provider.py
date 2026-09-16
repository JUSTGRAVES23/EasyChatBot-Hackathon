"""
OpenAI Speech Provider.

Concrete speech provider implementation for OpenAI.

Responsibilities:
- Transcribe audio using OpenAI speech-to-text.
- Synthesize speech using OpenAI text-to-speech.
- Hide OpenAI SDK details behind SpeechProvider.

Does NOT:
- Handle HTTP.
- Manage application workflows.
- Manage LiveKit.
- Persist conversations.
- Execute AI agents.
"""

from __future__ import annotations


import io


import os


from typing import Any


from openai import OpenAI


from app.providers.speech.speech_provider import (
    SpeechProvider,
)



class OpenAISpeechProvider(
    SpeechProvider,
):
    """
    OpenAI implementation of the speech provider contract.

    The OpenAI client is created lazily so that importing
    the provider and running unit tests does not require
    OPENAI_API_KEY to be present.

    A client can also be injected for testing.
    """


    DEFAULT_TRANSCRIPTION_MODEL = (
        "gpt-4o-mini-transcribe"
    )


    DEFAULT_TTS_MODEL = (
        "gpt-4o-mini-tts"
    )


    DEFAULT_VOICE = (
        "alloy"
    )


    def __init__(
        self,
        *,
        client: Any | None = None,
        transcription_model: str | None = None,
        tts_model: str | None = None,
    ) -> None:
        """
        Initialize the OpenAI speech provider.

        Parameters
        ----------
        client:
            Optional OpenAI client.

            Primarily intended for tests and dependency
            injection.

        transcription_model:
            Optional OpenAI transcription model.

        tts_model:
            Optional OpenAI text-to-speech model.
        """

        self._client = client

        self._transcription_model = (
            transcription_model
            or os.getenv(
                "OPENAI_TRANSCRIPTION_MODEL",
                self.DEFAULT_TRANSCRIPTION_MODEL,
            )
        )

        self._tts_model = (
            tts_model
            or os.getenv(
                "OPENAI_TTS_MODEL",
                self.DEFAULT_TTS_MODEL,
            )
        )


    @property
    def client(self) -> OpenAI:
        """
        Return the configured OpenAI client.

        The client is initialized lazily.
        """

        if self._client is None:

            api_key = os.getenv(
                "OPENAI_API_KEY"
            )

            if not api_key:

                raise RuntimeError(
                    "OPENAI_API_KEY is not configured."
                )

            self._client = OpenAI(
                api_key=api_key,
            )

        return self._client


    def transcribe(
        self,
        *,
        audio: bytes,
        language_code: str,
    ) -> str:
        """
        Transcribe audio into text.

        Parameters
        ----------
        audio:
            Raw audio bytes.

        language_code:
            ISO language code, for example ``fr``.

        Returns
        -------
        str
            Transcribed text.
        """

        if not audio:

            raise ValueError(
                "audio cannot be empty."
            )


        if not language_code.strip():

            raise ValueError(
                "language_code cannot be empty."
            )


        audio_file = io.BytesIO(
            audio
        )


        audio_file.name = (
            "voice_input.wav"
        )


        response = (
            self.client
            .audio
            .transcriptions
            .create(
                model=(
                    self._transcription_model
                ),
                file=audio_file,
                language=(
                    language_code
                ),
            )
        )


        text = getattr(
            response,
            "text",
            None,
        )


        if text is None:

            raise RuntimeError(
                "OpenAI transcription response "
                "did not contain text."
            )


        return str(text)



    def synthesize(
        self,
        *,
        text: str,
        voice_profile: str,
        language_code: str,
    ) -> bytes:
        """
        Generate speech audio.

        Parameters
        ----------
        text:
            Text to synthesize.

        voice_profile:
            Character voice profile.

        language_code:
            Language requested by the caller.

        Returns
        -------
        bytes
            Generated audio bytes.
        """

        if not text.strip():

            raise ValueError(
                "text cannot be empty."
            )


        if not voice_profile.strip():

            raise ValueError(
                "voice_profile cannot be empty."
            )


        if not language_code.strip():

            raise ValueError(
                "language_code cannot be empty."
            )


        # Character voice profiles are currently mapped
        # to provider-supported voices at the infrastructure
        # boundary. This prevents provider-specific voice
        # identifiers from leaking into the domain/runtime.
        voice = self._resolve_voice(
            voice_profile
        )


        response = (
            self.client
            .audio
            .speech
            .create(
                model=(
                    self._tts_model
                ),
                voice=voice,
                input=text,
                response_format="pcm",
            )
        )


        audio_content = getattr(
            response,
            "content",
            None,
        )


        if audio_content is not None:

            return bytes(
                audio_content
            )


        if hasattr(
            response,
            "read",
        ):

            return bytes(
                response.read()
            )


        raise RuntimeError(
            "OpenAI speech response "
            "did not contain audio content."
        )



    @classmethod
    def _resolve_voice(
        cls,
        voice_profile: str,
    ) -> str:
        """
        Map an application character voice profile
        to an OpenAI-supported voice.

        Character identifiers such as ``yeti`` must not
        be sent directly to the provider because they are
        application concepts rather than provider voice IDs.
        """

        normalized = (
            voice_profile
            .strip()
            .lower()
        )


        voice_mapping = {
            "yeti": "onyx",
        }


        return voice_mapping.get(
            normalized,
            normalized
            if normalized in {
                "alloy",
                "ash",
                "ballad",
                "coral",
                "echo",
                "fable",
                "nova",
                "onyx",
                "sage",
                "shimmer",
                "verse",
                "marin",
                "cedar",
            }
            else cls.DEFAULT_VOICE,
        )



__all__ = [
    "OpenAISpeechProvider",
]
