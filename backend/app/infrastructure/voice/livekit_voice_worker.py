"""
LiveKit Voice Worker.

Infrastructure entry point for realtime voice sessions.

Responsibilities:
- Receive a LiveKit job context.
- Read application-approved job metadata.
- Convert metadata into a voice call request.
- Build the existing EasyChatBot voice execution context.
- Build the existing UAI InteractionContext.
- Create the LiveKit realtime character agent.
- Start the LiveKit AgentSession.

Does NOT:
- Own EasyChatBot business logic.
- Resolve worlds or characters directly.
- Decide learner authorization.
- Persist conversations.
- Manage call lifecycle state.
- Bypass the EasyChatBot Runtime.
"""

from __future__ import annotations


# =========================================================
# Configuration
# =========================================================

from pathlib import Path
import os


from dotenv import load_dotenv



PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[4]
)


ENV_FILE = (
    PROJECT_ROOT
    / ".env"
)


load_dotenv(
    ENV_FILE
)



def _validate_livekit_configuration() -> None:
    """
    Validate required LiveKit configuration.
    """

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



# =========================================================
# Standard library
# =========================================================

import json
import logging


from dataclasses import dataclass



# =========================================================
# LiveKit
# =========================================================

from livekit.agents import (
    AgentServer,
    JobContext,
    cli,
)



# =========================================================
# Application layer
# =========================================================

from backend.app.application.uai.voice.voice_call_context_factory import (
    VoiceCallContextFactory,
)


from backend.app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)


from backend.app.application.uai.voice.voice_interaction_context_service import (
    VoiceInteractionContextService,
)


from backend.app.application.uai.voice.voice_dependencies import (
    build_voice_interaction_context_service,
)



# =========================================================
# AI Runtime
# =========================================================

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)


from backend.app.application.uai.voice.voice_ai_dependencies import (
    build_conversation_runtime,
)



# =========================================================
# Infrastructure
# =========================================================

from app.infrastructure.voice.livekit_realtime_agent import (
    LiveKitRealtimeAgent,
)



logger = logging.getLogger(
    __name__
)



@dataclass(
    frozen=True,
    slots=True,
)
class LiveKitVoiceWorker:
    """
    Infrastructure worker for EasyChatBot realtime voice.

    Dependencies are injected through composition.
    """

    context_factory: VoiceCallContextFactory


    interaction_context_service: (
        VoiceInteractionContextService
    )


    conversation_runtime: ConversationRuntime



    async def run(
        self,
        *,
        ctx: JobContext,
    ) -> None:
        """
        Connect to LiveKit and start
        EasyChatBot realtime character session.
        """


        metadata = (
            self._read_job_metadata(
                ctx,
            )
        )


        request = (
            self._create_voice_call_request(
                metadata,
            )
        )



        execution_context = (
            self.context_factory.create(
                request=request,
            )
        )



        interaction_context = (
            self.interaction_context_service.build(
                context=execution_context,
            )
        )



        character = (
            interaction_context.character
        )



        instructions = (
            "You are "
            f"{character.name}. "
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
            conversation_runtime=(
                self.conversation_runtime
            ),
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



        agent = (
            realtime_agent.create_agent()
        )



        session = (
            realtime_agent.create_session()
        )



        await session.start(
            agent=agent,
            room=ctx.room,
        )



    @staticmethod
    def _read_job_metadata(
        ctx: JobContext,
    ) -> dict[str, object]:
        """
        Read and validate LiveKit job metadata.
        """


        raw_metadata = (
            ctx.job.metadata
        )



        if not raw_metadata:
            raise ValueError(
                "LiveKit job metadata is required."
            )



        try:

            metadata = json.loads(
                raw_metadata,
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                "LiveKit job metadata must be valid JSON."
            ) from exc



        if not isinstance(
            metadata,
            dict,
        ):

            raise ValueError(
                "LiveKit job metadata must be a JSON object."
            )



        return metadata



    @staticmethod
    def _create_voice_call_request(
        metadata: dict[str, object],
    ) -> VoiceCallRequest:
        """
        Convert LiveKit metadata into
        application request contract.
        """


        required_fields = (
            "learner_id",
            "world_id",
            "character_id",
            "language_code",
        )



        values: dict[str, str] = {}



        for field in required_fields:

            value = metadata.get(
                field,
            )



            if not isinstance(
                value,
                str,
            ):

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



# =========================================================
# LiveKit Server
# =========================================================

server = AgentServer()



_worker = LiveKitVoiceWorker(
    context_factory=(
        VoiceCallContextFactory()
    ),

    interaction_context_service=(
        build_voice_interaction_context_service()
    ),

    conversation_runtime=(
        build_conversation_runtime()
    ),
)



@server.rtc_session(
    agent_name="easychatbot-voice",
)
async def entrypoint(
    ctx: JobContext,
) -> None:
    """
    LiveKit Agents entrypoint.
    """


    await _worker.run(
        ctx=ctx,
    )



def run() -> None:
    """
    Start LiveKit Agents worker.
    """


    cli.run_app(
        server,
    )



__all__ = [
    "LiveKitVoiceWorker",
    "entrypoint",
    "run",
]



if __name__ == "__main__":
    run()
