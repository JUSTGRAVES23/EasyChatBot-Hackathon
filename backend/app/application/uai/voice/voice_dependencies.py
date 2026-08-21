"""
Voice Dependency Composition.

Application composition root
for voice call services.

Responsibilities:
- Build voice dependencies.
- Wire application services.
- Build the UAI interaction-context bridge.

Does NOT:
- Handle HTTP.
- Execute calls.
- Persist data.
- Manage LiveKit directly.
"""

from __future__ import annotations


from pathlib import Path


from backend.app.application.uai.voice.voice_call_service import (
    VoiceCallService,
)


from backend.app.application.uai.voice.voice_call_orchestrator import (
    VoiceCallOrchestrator,
)


from backend.app.application.uai.voice.voice_character_session_service import (
    VoiceCharacterSessionService,
)


from backend.app.application.uai.voice.voice_interaction_context_service import (
    VoiceInteractionContextService,
)


from backend.app.application.uai.context.interaction_context_builder import (
    InteractionContextBuilder,
)


from backend.app.application.uai.world.world_resolver import (
    WorldResolver,
)


from backend.app.application.uai.character.character_resolver import (
    CharacterResolver,
)


from app.infrastructure.worlds.yaml_world_repository import (
    YamlWorldRepository,
)


from app.infrastructure.characters.yaml_character_repository import (
    YamlCharacterRepository,
)


from app.infrastructure.voice.livekit_adapter import (
    LiveKitAdapter,
)


from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)


from app.providers.speech.speech_provider_factory import (
    SpeechProviderFactory,
)


from app.configuration.providers.speech_provider_config import (
    SpeechProviderConfig,
)



def build_voice_call_service() -> VoiceCallService:
    """
    Create configured voice call service.
    """

    #
    # Application configuration root:
    #
    # backend/app
    #

    app_root = (
        Path(__file__)
        .resolve()
        .parents[3]
    )


    world_repository = YamlWorldRepository(
        worlds_path=(
            app_root
            / "configuration"
            / "worlds"
        )
    )


    character_repository = YamlCharacterRepository(
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


    context_builder = InteractionContextBuilder(
        world_resolver=WorldResolver(
            world_repository=world_repository,
        ),
        character_resolver=CharacterResolver(
            character_repository=character_repository,
        ),
    )


    #
    # Voice interaction-context bridge.
    #
    # Converts the existing voice call execution
    # context into the established UAI InteractionContext.
    #

    interaction_context_service = (
        VoiceInteractionContextService(
            context_builder=context_builder,
        )
    )


    #
    # LiveKit infrastructure boundary.
    #

    livekit_adapter = LiveKitAdapter()


    #
    # Speech provider configuration.
    #

    speech_config = SpeechProviderConfig(
        provider_name="openai",
        model_name="tts-1",
        default_language="fr",
    )


    speech_provider = (
        SpeechProviderFactory.create(
            config=speech_config,
        )
    )


    speech_runtime = VoiceSpeechRuntime(
        speech_provider=speech_provider,
    )


    session_service = VoiceCharacterSessionService(
        livekit_adapter=livekit_adapter,
        speech_runtime=speech_runtime,
    )


    orchestrator = VoiceCallOrchestrator(
        context_builder=context_builder,
        session_service=session_service,
    )


    #
    # Keep the interaction-context bridge available
    # through the composition root for realtime voice
    # infrastructure.
    #
    # The existing VoiceCallService contract remains
    # unchanged.
    #

    _ = interaction_context_service


    return VoiceCallService(
        orchestrator=orchestrator,
    )



def build_voice_interaction_context_service(
) -> VoiceInteractionContextService:
    """
    Build the application service that converts
    a voice execution context into InteractionContext.

    This is the composition entry point for
    realtime voice infrastructure.
    """

    app_root = (
        Path(__file__)
        .resolve()
        .parents[3]
    )


    world_repository = YamlWorldRepository(
        worlds_path=(
            app_root
            / "configuration"
            / "worlds"
        )
    )


    character_repository = YamlCharacterRepository(
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


    context_builder = InteractionContextBuilder(
        world_resolver=WorldResolver(
            world_repository=world_repository,
        ),
        character_resolver=CharacterResolver(
            character_repository=character_repository,
        ),
    )


    return VoiceInteractionContextService(
        context_builder=context_builder,
    )



__all__ = [
    "build_voice_call_service",
    "build_voice_interaction_context_service",
]
