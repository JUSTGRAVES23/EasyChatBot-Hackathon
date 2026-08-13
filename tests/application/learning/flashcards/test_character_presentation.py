from src.application.experience.flashcards.models import (
    CharacterPresentationContext,
)


def test_character_presentation_context_supports_image_url():

    character = CharacterPresentationContext(
        character_id="yeti",
        character_name="Yeti",
        opening_phrase="Look what I found! 🧊",
        tone="enthusiastic and curious",
        image_url="/characters/yeti.png",
    )

    assert character.character_id == "yeti"

    assert character.image_url == (
        "/characters/yeti.png"
    )


def test_character_presentation_image_is_optional():

    character = CharacterPresentationContext(
        character_id="clara",
        character_name="Clara",
        opening_phrase=(
            "I found something worth considering."
        ),
        tone="analytical and structured",
    )

    assert character.image_url is None