"""
Tests for InteractionContext.
"""

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


def create_test_context():

    return InteractionContext(
        learner=LearnerContext(
            learner_id="user123",
        ),

        world=WorldContext(
            world_id="french_world",
            name="French World",
            language_code="fr",
        ),

        character=CharacterContext(
            character_id="yeti",
            name="Yeti",
            personality_reference="friendly",
            teaching_style="supportive",
        ),

        voice=VoiceContext(
            language_code="fr",
            voice_provider="openai",
            voice_profile="yeti_fr",
        ),
    )


def test_interaction_context_creation():

    context = create_test_context()

    assert (
        context.character.character_id
        == "yeti"
    )


def test_context_is_immutable():

    context = create_test_context()

    try:

        context.world_id = "spanish_world"

        assert False

    except AttributeError:

        assert True