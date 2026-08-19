"""
Tests for Voice Session Service.
"""

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


def create_interaction_context() -> InteractionContext:
    """
    Create test interaction context.
    """

    learner = LearnerContext(
        learner_id="learner-001",
        learning_goals=[
            "conversation",
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


def test_create_voice_session():

    service = VoiceSessionService()

    context = create_interaction_context()


    session = service.create_session(
        interaction_context=context,
    )


    assert session.session_id

    assert session.character_id == (
        "yeti"
    )

    assert session.language_code == (
        "fr"
    )

    assert session.room_name.startswith(
        "yeti-"
    )

    assert session.status == (
        "created"
    )