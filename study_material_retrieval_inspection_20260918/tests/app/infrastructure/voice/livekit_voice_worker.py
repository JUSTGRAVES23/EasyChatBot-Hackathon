"""
LiveKit Voice Worker.

Infrastructure entry point for realtime voice sessions.
"""

from __future__ import annotations

from pathlib import Path
import json
import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from livekit.agents import AgentServer, JobContext, cli

from app.application.provider_management.functionality_control_composition import (
    create_standalone_functionality_control_service,
)
from app.application.uai.voice.voice_call_context_factory import (
    VoiceCallContextFactory,
)
from app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)
from app.application.uai.context.interaction_context_builder import (
    InteractionContextBuilder,
)
from app.domain.uai.context.learner_context import (
    LearnerContext,
)
from app.domain.uai.context.voice_context import (
    VoiceContext,
)
from app.application.uai.voice.voice_ai_dependencies import (
    build_conversation_runtime,
    build_voice_speech_runtime,
)
from app.application.uai.world.world_resolver import (
    WorldResolver,
)
from app.application.uai.character.character_resolver import (
    CharacterResolver,
)
from app.infrastructure.worlds.yaml_world_repository import (
    YamlWorldRepository,
)
from app.infrastructure.characters.yaml_character_repository import (
    YamlCharacterRepository,
)
from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)
from app.infrastructure.voice.livekit_realtime_agent import (
    LiveKitRealtimeAgent,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env")


def _validate_livekit_configuration() -> None:
    """Validate required LiveKit configuration."""

    required = (
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
    )

    missing = [
        item
        for item in required
        if not os.getenv(item)
    ]

    if missing:
        raise RuntimeError(
            "Missing LiveKit configuration: "
            + ", ".join(missing)
        )


_validate_livekit_configuration()


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LiveKitVoiceWorker:
    """Infrastructure worker for EasyChatBot realtime voice."""

    context_factory: VoiceCallContextFactory
    interaction_context_builder: InteractionContextBuilder
    conversation_runtime: ConversationRuntime
    speech_runtime: VoiceSpeechRuntime

    async def run(
        self,
        *,
        ctx: JobContext,
    ) -> None:
        """Connect to LiveKit and start a realtime session."""

        metadata = self._read_job_metadata(ctx)

        request = self._create_voice_call_request(metadata)

        execution_context = self.context_factory.create(
            request=request,
        )

        learner = LearnerContext(
            learner_id=request.learner_id,
            learning_goals=("conversation",),
        )

        voice = VoiceContext(
            language_code=request.language_code,
            voice_provider="openai",
            voice_profile=request.character_id,
        )

        interaction_context = self.interaction_context_builder.build(
            learner=learner,
            world_id=request.world_id,
            character_id=request.character_id,
            voice=voice,
        )

        character = interaction_context.character

        instructions = (
            f"You are {character.name}. "
            "You are a French learning character. "
            "Your personality reference is "
            f"{character.personality_reference}. "
            "Your teaching style is "
            f"{character.teaching_style}. "
            "Speak naturally and help the learner "
            "practice the target language."
        )

        realtime_agent = LiveKitRealtimeAgent(
            context=interaction_context,
            instructions=instructions,
            conversation_runtime=self.conversation_runtime,
            speech_runtime=self.speech_runtime,
        )

        ctx.log_context_fields = {
            "room_name": ctx.room.name,
            "learner_id": request.learner_id,
            "world_id": request.world_id,
            "character_id": request.character_id,
            "language_code": request.language_code,
        }

        logger.info(
            "Starting EasyChatBot LiveKit voice agent",
            extra={
                "room_name": ctx.room.name,
                "learner_id": request.learner_id,
                "world_id": request.world_id,
                "character_id": request.character_id,
                "language_code": request.language_code,
            },
        )

        await ctx.connect()

        agent = realtime_agent.create_agent()
        session = realtime_agent.create_session()

        await session.start(
            agent=agent,
            room=ctx.room,
        )

    @staticmethod
    def _read_job_metadata(
        ctx: JobContext,
    ) -> dict[str, object]:
        """Read and validate LiveKit job metadata."""

        raw_metadata = ctx.job.metadata

        if not raw_metadata:
            raise ValueError(
                "LiveKit job metadata is required."
            )

        try:
            metadata = json.loads(raw_metadata)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "LiveKit job metadata must be valid JSON."
            ) from exc

        if not isinstance(metadata, dict):
            raise ValueError(
                "LiveKit job metadata must be a JSON object."
            )

        return metadata

    @staticmethod
    def _create_voice_call_request(
        metadata: dict[str, object],
    ) -> VoiceCallRequest:
        """Convert LiveKit metadata into application request."""

        required_fields = (
            "learner_id",
            "world_id",
            "character_id",
            "language_code",
        )

        values: dict[str, str] = {}

        for field in required_fields:
            value = metadata.get(field)

            if not isinstance(value, str):
                raise ValueError(
                    f"LiveKit metadata field "
                    f"'{field}' must be a string."
                )

            if not value.strip():
                raise ValueError(
                    f"LiveKit metadata field "
                    f"'{field}' cannot be empty."
                )

            values[field] = value.strip()

        return VoiceCallRequest(
            learner_id=values["learner_id"],
            world_id=values["world_id"],
            character_id=values["character_id"],
            language_code=values["language_code"],
        )


server = AgentServer()

_functionality_control_service, _control_engine = (
    create_standalone_functionality_control_service()
)

_worker = LiveKitVoiceWorker(
    context_factory=VoiceCallContextFactory(),
    interaction_context_builder=InteractionContextBuilder(
        world_resolver=WorldResolver(
            world_repository=YamlWorldRepository(
                worlds_path=(
                    PROJECT_ROOT
                    / "backend"
                    / "app"
                    / "configuration"
                    / "worlds"
                )
            )
        ),
        character_resolver=CharacterResolver(
            character_repository=YamlCharacterRepository(
                profiles_path=(
                    Path(
                        r"C:\AI Folder\FrenchTeacherAI"
                    )
                    / "docs"
                    / "specifications"
                    / "characters"
                    / "profiles"
                )
            )
        ),
    ),
    conversation_runtime=build_conversation_runtime(),
    speech_runtime=build_voice_speech_runtime(
        functionality_control_service=(
            _functionality_control_service
        ),
    ),
)


@server.rtc_session(
    agent_name="easychatbot-voice",
)
async def entrypoint(
    ctx: JobContext,
) -> None:
    """LiveKit Agents entrypoint."""

    await _worker.run(ctx=ctx)


def run() -> None:
    """Start LiveKit Agents worker."""

    try:
        cli.run_app(server)
    finally:
        _control_engine.dispose()


__all__ = [
    "LiveKitVoiceWorker",
    "entrypoint",
    "run",
]


if __name__ == "__main__":
    run()


