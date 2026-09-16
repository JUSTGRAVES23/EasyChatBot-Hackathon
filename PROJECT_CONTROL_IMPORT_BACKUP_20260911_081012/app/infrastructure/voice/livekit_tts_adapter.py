"""LiveKit TTS adapter for EasyChatBot."""

from __future__ import annotations

from livekit.agents import APIConnectOptions
from livekit.agents.tts import (
    AudioEmitter,
    ChunkedStream,
    TTS,
    TTSCapabilities,
)

from app.ai_runtime.voice.voice_speech_runtime import VoiceSpeechRuntime


class LiveKitTTSAdapter(TTS):
    """Expose EasyChatBot VoiceSpeechRuntime as LiveKit TTS."""

    def __init__(
        self,
        *,
        speech_runtime: VoiceSpeechRuntime,
        voice_profile: str = "alloy",
        language_code: str = "fr",
        sample_rate: int = 24000,
        num_channels: int = 1,
    ) -> None:
        super().__init__(
            capabilities=TTSCapabilities(
                streaming=False,
            ),
            sample_rate=sample_rate,
            num_channels=num_channels,
        )

        if not language_code.strip():
            raise ValueError(
                "language_code cannot be empty."
            )

        self._speech_runtime = speech_runtime
        self._voice_profile = voice_profile
        self._language_code = language_code

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = APIConnectOptions(),
    ) -> ChunkedStream:
        return _LiveKitTTSChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
            speech_runtime=self._speech_runtime,
            voice_profile=self._voice_profile,
            language_code=self._language_code,
        )


class _LiveKitTTSChunkedStream(ChunkedStream):
    """Adapt complete provider audio bytes to LiveKit AudioEmitter."""

    def __init__(
        self,
        *,
        tts: TTS,
        input_text: str,
        conn_options: APIConnectOptions,
        speech_runtime: VoiceSpeechRuntime,
        voice_profile: str,
        language_code: str,
    ) -> None:
        super().__init__(
            tts=tts,
            input_text=input_text,
            conn_options=conn_options,
        )

        self._speech_runtime = speech_runtime
        self._voice_profile = voice_profile
        self._language_code = language_code

    async def _run(
        self,
        output_emitter: AudioEmitter,
    ) -> None:
        audio = self._speech_runtime.synthesize(
            text=self.input_text,
            voice_profile=self._voice_profile,
            language_code=self._language_code,
        )

        output_emitter.initialize(
            request_id="",
            sample_rate=self._tts.sample_rate,
            num_channels=self._tts.num_channels,
            mime_type="audio/pcm",
        )

        output_emitter.push(audio)
        output_emitter.end_input()


__all__ = ["LiveKitTTSAdapter"]

