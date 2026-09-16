"""
Tests for the LiveKit Voice Worker.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from livekit.agents import JobContext

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)
from app.infrastructure.voice.livekit_voice_worker import (
    LiveKitVoiceWorker,
)
from app.application.uai.context.interaction_context_builder import (
    InteractionContextBuilder,
)


def create_job_context(
    *,
    metadata: dict[str, object] | None = None,
) -> Mock:
    ctx = Mock(spec=JobContext)

    ctx.job = Mock()
    ctx.job.metadata = (
        json.dumps(metadata)
        if metadata is not None
        else ""
    )

    ctx.room = Mock()
    ctx.room.name = "test-room"

    ctx.connect = AsyncMock()

    return ctx


def create_interaction_context() -> Mock:
    character = Mock()
    character.name = "Yeti"
    character.personality_reference = "friendly"
    character.teaching_style = "supportive"

    context = Mock()
    context.character = character

    return context


def create_worker() -> LiveKitVoiceWorker:
    return LiveKitVoiceWorker(
        context_factory=Mock(),
        interaction_context_builder=Mock(
            spec=InteractionContextBuilder,
        ),
        conversation_runtime=Mock(
            spec=ConversationRuntime,
        ),
        speech_runtime=Mock(
            spec=VoiceSpeechRuntime,
        ),
    )


def test_read_job_metadata_requires_metadata():
    ctx = create_job_context()

    with pytest.raises(
        ValueError,
        match="LiveKit job metadata is required",
    ):
        LiveKitVoiceWorker._read_job_metadata(ctx)


def test_read_job_metadata_requires_valid_json():
    ctx = create_job_context()
    ctx.job.metadata = "{invalid-json"

    with pytest.raises(
        ValueError,
        match="must be valid JSON",
    ):
        LiveKitVoiceWorker._read_job_metadata(ctx)


def test_read_job_metadata_requires_json_object():
    ctx = create_job_context()
    ctx.job.metadata = json.dumps(
        ["invalid"],
    )

    with pytest.raises(
        ValueError,
        match="must be a JSON object",
    ):
        LiveKitVoiceWorker._read_job_metadata(ctx)


def test_create_voice_call_request_requires_all_fields():
    metadata = {
        "learner_id": "learner-1",
        "world_id": "academy",
        "character_id": "yeti",
    }

    with pytest.raises(
        ValueError,
        match="'language_code' must be a string",
    ):
        LiveKitVoiceWorker._create_voice_call_request(
            metadata,
        )


def test_create_voice_call_request_rejects_empty_values():
    metadata = {
        "learner_id": "learner-1",
        "world_id": "academy",
        "character_id": "yeti",
        "language_code": " ",
    }

    with pytest.raises(
        ValueError,
        match="'language_code' cannot be empty",
    ):
        LiveKitVoiceWorker._create_voice_call_request(
            metadata,
        )


def test_create_voice_call_request_preserves_values():
    metadata = {
        "learner_id": " learner-1 ",
        "world_id": " academy ",
        "character_id": " yeti ",
        "language_code": " fr ",
    }

    request = (
        LiveKitVoiceWorker._create_voice_call_request(
            metadata,
        )
    )

    assert request.learner_id == "learner-1"
    assert request.world_id == "academy"
    assert request.character_id == "yeti"
    assert request.language_code == "fr"


@pytest.mark.asyncio
async def test_run_wires_conversation_and_speech_runtime():
    worker = create_worker()

    ctx = create_job_context(
        metadata={
            "learner_id": "learner-1",
            "world_id": "academy",
            "character_id": "yeti",
            "language_code": "fr",
        }
    )

    execution_context = Mock()
    interaction_context = (
        create_interaction_context()
    )

    worker.context_factory.create.return_value = (
        execution_context
    )
    worker.interaction_context_builder.build.return_value = (
        interaction_context
    )

    agent = Mock()
    session = Mock()
    session.start = AsyncMock()

    with patch(
        "app.infrastructure.voice.livekit_voice_worker.LiveKitRealtimeAgent"
    ) as realtime_agent_class:
        realtime_agent = (
            realtime_agent_class.return_value
        )
        realtime_agent.create_agent.return_value = agent
        realtime_agent.create_session.return_value = (
            session
        )

        await worker.run(ctx=ctx)

    realtime_agent_class.assert_called_once_with(
        context=interaction_context,
        instructions=(
            "You are Yeti. "
            "You are a French learning character. "
            "Your personality reference is friendly. "
            "Your teaching style is supportive. "
            "Speak naturally and help the learner "
            "practice the target language."
        ),
        conversation_runtime=worker.conversation_runtime,
        speech_runtime=worker.speech_runtime,
    )

    ctx.connect.assert_awaited_once()

    realtime_agent.create_agent.assert_called_once()
    realtime_agent.create_session.assert_called_once()

    session.start.assert_awaited_once_with(
        agent=agent,
        room=ctx.room,
    )


@pytest.mark.asyncio
async def test_run_rejects_invalid_metadata_before_connecting():
    worker = create_worker()

    ctx = create_job_context(
        metadata={
            "learner_id": "learner-1",
            "world_id": "academy",
            "character_id": "yeti",
        }
    )

    with pytest.raises(
        ValueError,
        match="'language_code' must be a string",
    ):
        await worker.run(ctx=ctx)

    ctx.connect.assert_not_awaited()

