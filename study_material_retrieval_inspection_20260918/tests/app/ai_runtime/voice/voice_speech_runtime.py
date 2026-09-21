"""Voice Speech Runtime."""

from __future__ import annotations

from dataclasses import dataclass

from app.ai_runtime.voice.functionality_control_port import (
    FunctionalityControlPort,
)
from app.providers.speech.speech_provider import SpeechProvider


@dataclass(frozen=True, slots=True)
class VoiceSpeechRuntime:
    """Runtime service for provider-independent speech operations."""

    speech_provider: SpeechProvider
    functionality_control_service: FunctionalityControlPort | None = None

    VOICE_TTS_FUNCTIONALITY_ID = "voice_tts"
    VOICE_TTS_ENVIRONMENT = "adults"

    def _ensure_functionality_enabled(self) -> None:
        """Fail closed when central Voice/TTS control is unavailable."""

        control_service = self.functionality_control_service

        if control_service is None:
            return

        try:
            availability = control_service.get_availability(
                environment=self.VOICE_TTS_ENVIRONMENT,
                functionality_id=self.VOICE_TTS_FUNCTIONALITY_ID,
            )
        except Exception as exc:
            raise RuntimeError(
                "Voice/TTS operational control could not be verified."
            ) from exc

        if availability != "enabled":
            raise RuntimeError(
                "Voice/TTS functionality is currently unavailable."
            )

    def transcribe(
        self,
        *,
        audio: bytes,
        language_code: str,
    ) -> str:
        """Convert audio input into text."""

        self._ensure_functionality_enabled()

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
        """Convert text into generated audio."""

        self._ensure_functionality_enabled()

        return self.speech_provider.synthesize(
            text=text,
            voice_profile=voice_profile,
            language_code=language_code,
        )


__all__ = ["VoiceSpeechRuntime"]

