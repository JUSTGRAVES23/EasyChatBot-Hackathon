"""
Tests for Voice Session Orchestrator.
"""

from app.application.uai.voice.voice_session_orchestrator import (
    VoiceSessionOrchestrator,
)

from app.application.uai.voice.voice_session_service import (
    VoiceSessionService,
)

from app.domain.uai.context.character_context import (
    CharacterContext,
)

from app.domain.uai.context.interaction_context import (
    InteractionContext,
)

from app.domain.uai.context.learner_context import (
    LearnerContext,
)

from app.domain.uai.context.voice_context import (
    VoiceContext,
)

from app.domain.uai.context.world_context import (
    WorldContext,
)

from app.infrastructure.voice.livekit_adapter import (
    LiveKitAdapter,
)


def create_interaction_context() -> InteractionContext:
    """
    Create valid interaction context.
    """

    learner = LearnerContext(
        learner_id="learner-001",
        learning_goals=[
            "conversation",
            "pronunciation",
        ],
    )


    world = WorldContext(
        world_id="french_world",
        name="French World",
        language_code="fr",
        available_characters=[
            "yeti",
            "alix",
        ],
    )


    character = CharacterContext(
        character_id="yeti",
        name="Yeti",
        personality_reference="Storyteller",
        teaching_style="Story-driven",
    )


    voice = VoiceContext(
        language_code="fr",
        voice_provider="openai",
        voice_profile="verse",
    )


    return InteractionContext(
        learner=learner,
        world=world,
        character=character,
        voice=voice,
    )


def test_prepare_voice_session():

    orchestrator = VoiceSessionOrchestrator(
        voice_session_service=(
            VoiceSessionService()
        ),
        livekit_adapter=(
            LiveKitAdapter()
        ),
    )


    context = (
        create_interaction_context()
    )


    configuration = (
        orchestrator.prepare_session(
            interaction_context=context,
        )
    )


    assert configuration["provider"] == (
        "livekit"
    )


    assert configuration["character_id"] == (
        "yeti"
    )


    assert configuration["language_code"] == (
        "fr"
    )


    assert configuration["room_name"].startswith(
        "yeti-"
    )