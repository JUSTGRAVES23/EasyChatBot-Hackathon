"""
Tests for Voice Character Agent.
"""

from app.ai_runtime.voice.voice_character_agent import (
    VoiceCharacterAgent,
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
        personality_reference=(
            "storyteller"
        ),
        teaching_style=(
            "narrative learning"
        ),
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



def test_voice_character_agent_keeps_character_identity():

    context = (
        create_interaction_context()
    )


    agent = VoiceCharacterAgent(
        context=context
    )


    assert agent.get_character_id() == (
        "yeti"
    )


    assert agent.get_language_code() == (
        "fr"
    )