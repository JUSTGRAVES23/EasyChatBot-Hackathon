"""
Tests for Interaction Context Builder.
"""

from pathlib import Path

from app.application.uai.character.character_resolver import (
    CharacterResolver,
)

from app.application.uai.context.interaction_context_builder import (
    InteractionContextBuilder,
)

from app.application.uai.world.world_resolver import (
    WorldResolver,
)

from app.domain.uai.context.learner_context import (
    LearnerContext,
)

from app.domain.uai.context.voice_context import (
    VoiceContext,
)

from app.infrastructure.characters.yaml_character_repository import (
    YamlCharacterRepository,
)

from app.infrastructure.worlds.yaml_world_repository import (
    YamlWorldRepository,
)


WORLD_CONFIG_PATH = (
    Path(__file__)
    .resolve()
    .parents[4]
    / "app"
    / "configuration"
    / "worlds"
)


CHARACTER_PROFILE_PATH = (
    Path(
        r"C:\AI Folder\FrenchTeacherAI"
    )
    / "docs"
    / "specifications"
    / "characters"
    / "profiles"
)


def test_build_interaction_context():

    print(
        "WORLD CONFIG PATH:",
        WORLD_CONFIG_PATH,
    )

    print(
        "WORLD CONFIG EXISTS:",
        WORLD_CONFIG_PATH.exists(),
    )

    print(
        "WORLD CONFIG FILES:",
        list(
            WORLD_CONFIG_PATH.glob("*")
        ),
    )


    world_repository = YamlWorldRepository(
        worlds_path=WORLD_CONFIG_PATH
    )

    character_repository = YamlCharacterRepository(
        profiles_path=CHARACTER_PROFILE_PATH
    )


    world_resolver = WorldResolver(
        world_repository=world_repository
    )

    character_resolver = CharacterResolver(
        character_repository=character_repository
    )


    builder = InteractionContextBuilder(
        world_resolver=world_resolver,
        character_resolver=character_resolver,
    )


    learner = LearnerContext(
        learner_id="learner-001",
        learning_goals=[
            "conversation",
            "pronunciation",
        ],
    )


    voice = VoiceContext(
        language_code="fr",
        voice_provider="openai",
        voice_profile="verse",
    )


    context = builder.build(
        learner=learner,
        world_id="french_world",
        character_id="yeti",
        voice=voice,
    )


    assert context.world.world_id == (
        "french_world"
    )

    assert context.world.language_code == (
        "fr"
    )


    assert context.character.character_id == (
        "yeti"
    )

    assert context.character.name == (
        "Yeti"
    )


    assert context.learner.learner_id == (
        "learner-001"
    )


    assert context.voice.language_code == (
        "fr"
    )

    assert context.voice.voice_provider == (
        "openai"
    )

    assert context.voice.voice_profile == (
        "verse"
    )

