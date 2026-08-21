"""
LiveKit Voice Runtime Adapter.

Infrastructure adapter between LiveKit realtime events
and the EasyChatBot AI Runtime voice layer.

Responsibilities:
- Bridge LiveKit audio events to VoiceSpeechRuntime.
- Keep LiveKit-specific handling inside infrastructure.
- Delegate speech operations to AI Runtime.
- Preserve provider independence.

Does NOT:
- Own AI conversation logic.
- Select speech providers.
- Store conversations.
- Manage learner authorization.
- Manage LiveKit rooms.
- Bypass EasyChatBot Runtime.
"""

from __future__ import annotations


import logging


from dataclasses import dataclass


from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)


logger = logging.getLogger(
    __name__
)


@dataclass(
    frozen=True,
    slots=True,
)
class LiveKitVoiceRuntimeAdapter:
    """
    Adapter between LiveKit and EasyChatBot voice runtime.

    LiveKit remains an infrastructure transport.
    VoiceSpeechRuntime remains the application/runtime
    abstraction for speech operations.
    """

    speech_runtime: VoiceSpeechRuntime


    async def transcribe_audio(
        self,
        *,
        audio: bytes,
        language_code: str,
    ) -> str:
        """
        Convert incoming LiveKit audio into text.

        Delegates processing to the configured
        SpeechProvider through VoiceSpeechRuntime.
        """

        logger.debug(
            "Transcribing LiveKit audio",
            extra={
                "language_code": language_code,
                "audio_size": len(audio),
            },
        )


        return self.speech_runtime.transcribe(
            audio=audio,
            language_code=language_code,
        )


    async def synthesize_text(
        self,
        *,
        text: str,
        voice_profile: str,
        language_code: str,
    ) -> bytes:
        """
        Convert generated text into audio.

        Delegates processing to the configured
        SpeechProvider through VoiceSpeechRuntime.
        """

        logger.debug(
            "Synthesizing LiveKit speech",
            extra={
                "language_code": language_code,
                "voice_profile": voice_profile,
                "text_length": len(text),
            },
        )


        return self.speech_runtime.synthesize(
            text=text,
            voice_profile=voice_profile,
            language_code=language_code,
        )


__all__ = [
    "LiveKitVoiceRuntimeAdapter",
]