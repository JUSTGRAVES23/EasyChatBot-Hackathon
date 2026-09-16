from __future__ import annotations

from unittest.mock import Mock

import pytest

from livekit.agents import APIConnectOptions
from livekit.agents.stt import SpeechEventType
from livekit.rtc import AudioFrame

from app.infrastructure.voice.livekit_stt_adapter import (
    LiveKitSTTAdapter,
)
from app.infrastructure.voice.livekit_tts_adapter import (
    LiveKitTTSAdapter,
)


class FakeSpeechRuntime:
    def __init__(
        self,
        *,
        transcription: str = "bonjour",
        synthesized_audio: bytes = b"audio",
    ) -> None:
        self.transcription = transcription
        self.synthesized_audio = synthesized_audio
        self.transcribe_calls: list[dict] = []
        self.synthesize_calls: list[dict] = []

    def transcribe(
        self,
        *,
        audio: bytes,
        language_code: str,
    ) -> str:
        self.transcribe_calls.append(
            {
                "audio": audio,
                "language_code": language_code,
            }
        )
        return self.transcription

    def synthesize(
        self,
        *,
        text: str,
        voice_profile: str,
        language_code: str,
    ) -> bytes:
        self.synthesize_calls.append(
            {
                "text": text,
                "voice_profile": voice_profile,
                "language_code": language_code,
            }
        )
        return self.synthesized_audio


@pytest.mark.asyncio
async def test_stt_adapter_transcribes_audio_frame() -> None:
    runtime = FakeSpeechRuntime(
        transcription="Bonjour tout le monde",
    )

    adapter = LiveKitSTTAdapter(
        speech_runtime=runtime,
        language_code="fr",
    )

    frame = AudioFrame(
        data=b"pcm-data",
        sample_rate=24000,
        num_channels=1,
        samples_per_channel=4,
    )

    event = await adapter._recognize_impl(
        [frame],
        language="fr",
        conn_options=APIConnectOptions(),
    )

    assert event.type is SpeechEventType.FINAL_TRANSCRIPT
    assert (
        event.alternatives[0].text
        == "Bonjour tout le monde"
    )
    assert event.alternatives[0].language == "fr"

    assert len(runtime.transcribe_calls) == 1

    audio = runtime.transcribe_calls[0]["audio"]

    assert audio[:4] == b"RIFF"
    assert audio[8:12] == b"WAVE"
    assert audio[12:16] == b"fmt "
    assert audio[36:40] == b"data"
    assert audio.endswith(b"pcm-data")

    assert (
        runtime.transcribe_calls[0]["language_code"]
        == "fr"
    )


@pytest.mark.asyncio
async def test_stt_adapter_uses_configured_language_when_livekit_language_missing(
) -> None:
    runtime = FakeSpeechRuntime()

    adapter = LiveKitSTTAdapter(
        speech_runtime=runtime,
        language_code="en-US",
    )

    frame = AudioFrame(
        data=b"\x01\x00\x02\x00",
        sample_rate=24000,
        num_channels=1,
        samples_per_channel=2,
    )

    event = await adapter._recognize_impl(
        [frame],
        language=None,
        conn_options=APIConnectOptions(),
    )

    assert event.alternatives[0].language == "en-US"
    assert (
        runtime.transcribe_calls[0]["language_code"]
        == "en-US"
    )


@pytest.mark.asyncio
async def test_stt_adapter_supports_non_french_language() -> None:
    runtime = FakeSpeechRuntime(
        transcription="Hello everyone",
    )

    adapter = LiveKitSTTAdapter(
        speech_runtime=runtime,
        language_code="en",
    )

    frame = AudioFrame(
        data=b"\x01\x00\x02\x00",
        sample_rate=24000,
        num_channels=1,
        samples_per_channel=2,
    )

    event = await adapter._recognize_impl(
        [frame],
        language=None,
        conn_options=APIConnectOptions(),
    )

    assert event.alternatives[0].text == "Hello everyone"
    assert event.alternatives[0].language == "en"
    assert (
        runtime.transcribe_calls[0]["language_code"]
        == "en"
    )


@pytest.mark.asyncio
async def test_stt_adapter_supports_regional_language_code() -> None:
    runtime = FakeSpeechRuntime()

    adapter = LiveKitSTTAdapter(
        speech_runtime=runtime,
        language_code="es-MX",
    )

    frame = AudioFrame(
        data=b"\x01\x00\x02\x00",
        sample_rate=24000,
        num_channels=1,
        samples_per_channel=2,
    )

    event = await adapter._recognize_impl(
        [frame],
        language=None,
        conn_options=APIConnectOptions(),
    )

    assert event.alternatives[0].language == "es-MX"
    assert (
        runtime.transcribe_calls[0]["language_code"]
        == "es-MX"
    )


@pytest.mark.asyncio
async def test_stt_adapter_livekit_language_overrides_configured_language(
) -> None:
    runtime = FakeSpeechRuntime()

    adapter = LiveKitSTTAdapter(
        speech_runtime=runtime,
        language_code="en-US",
    )

    frame = AudioFrame(
        data=b"\x01\x00\x02\x00",
        sample_rate=24000,
        num_channels=1,
        samples_per_channel=2,
    )

    event = await adapter._recognize_impl(
        [frame],
        language="fr",
        conn_options=APIConnectOptions(),
    )

    assert event.alternatives[0].language == "fr"
    assert (
        runtime.transcribe_calls[0]["language_code"]
        == "fr"
    )


@pytest.mark.asyncio
async def test_stt_adapter_combines_multiple_audio_frames() -> None:
    runtime = FakeSpeechRuntime()

    adapter = LiveKitSTTAdapter(
        speech_runtime=runtime,
        language_code="fr",
    )

    frames = [
        AudioFrame(
            data=b"\x01\x00\x02\x00\x03\x00",
            sample_rate=24000,
            num_channels=1,
            samples_per_channel=3,
        ),
        AudioFrame(
            data=b"\x04\x00\x05\x00\x06\x00",
            sample_rate=24000,
            num_channels=1,
            samples_per_channel=3,
        ),
    ]

    await adapter._recognize_impl(
        frames,
        language=None,
        conn_options=APIConnectOptions(),
    )

    audio = runtime.transcribe_calls[0]["audio"]

    assert audio[:4] == b"RIFF"
    assert audio[8:12] == b"WAVE"
    assert audio[12:16] == b"fmt "
    assert audio[36:40] == b"data"

    assert audio.endswith(
        b"\x01\x00\x02\x00\x03\x00"
        b"\x04\x00\x05\x00\x06\x00"
    )

    assert (
        runtime.transcribe_calls[0]["language_code"]
        == "fr"
    )


@pytest.mark.asyncio
async def test_tts_adapter_delegates_to_runtime() -> None:
    runtime = FakeSpeechRuntime(
        synthesized_audio=b"pcm-audio",
    )

    adapter = LiveKitTTSAdapter(
        speech_runtime=runtime,
        voice_profile="yeti",
        language_code="fr",
    )

    stream = adapter.synthesize(
        "Bonjour",
        conn_options=APIConnectOptions(),
    )

    assert stream.input_text == "Bonjour"

    await stream.aclose()

    assert runtime.synthesize_calls == []


@pytest.mark.asyncio
async def test_tts_chunked_stream_synthesizes_and_emits_audio() -> None:
    runtime = FakeSpeechRuntime(
        synthesized_audio=b"pcm-audio",
    )

    adapter = LiveKitTTSAdapter(
        speech_runtime=runtime,
        voice_profile="yeti",
        language_code="fr",
        sample_rate=24000,
        num_channels=1,
    )

    stream = adapter.synthesize(
        "Bonjour",
        conn_options=APIConnectOptions(),
    )

    emitter = Mock()

    await stream._run(emitter)

    assert runtime.synthesize_calls == [
        {
            "text": "Bonjour",
            "voice_profile": "yeti",
            "language_code": "fr",
        }
    ]

    emitter.initialize.assert_called_once()
    emitter.push.assert_called_once_with(
        b"pcm-audio",
    )
    emitter.end_input.assert_called_once()


@pytest.mark.asyncio
async def test_tts_adapter_supports_non_french_language() -> None:
    runtime = FakeSpeechRuntime(
        synthesized_audio=b"pcm-audio",
    )

    adapter = LiveKitTTSAdapter(
        speech_runtime=runtime,
        voice_profile="alex",
        language_code="en-US",
    )

    stream = adapter.synthesize(
        "Hello",
        conn_options=APIConnectOptions(),
    )

    emitter = Mock()

    await stream._run(emitter)

    assert runtime.synthesize_calls == [
        {
            "text": "Hello",
            "voice_profile": "alex",
            "language_code": "en-US",
        }
    ]

    await stream.aclose()