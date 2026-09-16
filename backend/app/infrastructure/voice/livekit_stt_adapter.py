"""
LiveKit STT adapter for EasyChatBot.
"""

from __future__ import annotations

import io
import wave

from livekit.agents import APIConnectOptions
from livekit.agents.stt import (
    STT,
    STTCapabilities,
    SpeechData,
    SpeechEvent,
    SpeechEventType,
)
from livekit.agents.stt.stt import AudioBuffer

from app.ai_runtime.voice.voice_speech_runtime import VoiceSpeechRuntime


class LiveKitSTTAdapter(STT):
    """Expose EasyChatBot VoiceSpeechRuntime as LiveKit STT."""

    def __init__(
        self,
        *,
        speech_runtime: VoiceSpeechRuntime,
        language_code: str,
    ) -> None:
        super().__init__(
            capabilities=STTCapabilities(
                streaming=False,
                interim_results=False,
                offline_recognize=True,
            )
        )

        if not language_code.strip():
            raise ValueError(
                "language_code cannot be empty."
            )

        self._speech_runtime = speech_runtime
        self._language_code = language_code.strip()

    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: str | None = None,
        conn_options: APIConnectOptions,
    ) -> SpeechEvent:
        frames = (
            buffer
            if isinstance(buffer, list)
            else [buffer]
        )

        if not frames:
            raise ValueError(
                "LiveKit audio buffer cannot be empty."
            )

        audio = b"".join(
            bytes(frame.data)
            for frame in frames
        )

        if not audio:
            raise ValueError(
                "LiveKit audio buffer cannot be empty."
            )

        first_frame = frames[0]

        sample_rate = int(first_frame.sample_rate)
        num_channels = int(first_frame.num_channels)

        if sample_rate <= 0:
            raise ValueError(
                "LiveKit audio sample rate must be positive."
            )

        if num_channels <= 0:
            raise ValueError(
                "LiveKit audio channel count must be positive."
            )

        bytes_per_frame = num_channels * 2

        if len(audio) % bytes_per_frame != 0:
            raise ValueError(
                "LiveKit audio buffer is not aligned "
                "to 16-bit PCM samples."
            )

        for frame in frames[1:]:
            frame_sample_rate = int(frame.sample_rate)
            frame_num_channels = int(
                frame.num_channels
            )

            if frame_sample_rate != sample_rate:
                raise ValueError(
                    "LiveKit audio frames must use "
                    "the same sample rate."
                )

            if frame_num_channels != num_channels:
                raise ValueError(
                    "LiveKit audio frames must use "
                    "the same channel count."
                )

        wav_buffer = io.BytesIO()

        with wave.open(
            wav_buffer,
            "wb",
        ) as wav_file:
            wav_file.setnchannels(
                num_channels,
            )
            wav_file.setsampwidth(2)
            wav_file.setframerate(
                sample_rate,
            )
            wav_file.writeframes(audio)

        wav_audio = wav_buffer.getvalue()

        language_code = (
            language.strip()
            if language is not None
            and language.strip()
            else self._language_code
        )

        text = self._speech_runtime.transcribe(
            audio=wav_audio,
            language_code=language_code,
        )

        return SpeechEvent(
            type=SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[
                SpeechData(
                    language=language_code,
                    text=text,
                )
            ],
        )


__all__ = ["LiveKitSTTAdapter"]
