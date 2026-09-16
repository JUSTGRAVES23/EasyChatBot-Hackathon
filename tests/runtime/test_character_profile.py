from characters.character_profile import (
    CharacterProfile,
)


def test_character_profile():

    character = CharacterProfile(
        character_id="yeti",
        name="Yeti",
        description=(
            "A friendly AI learning companion"
        ),
        personality=(
            "Curious and encouraging"
        ),
        learning_style=(
            "Conversation based learning"
        ),
    )

    assert character.name == "Yeti"

    assert (
        character.learning_style
        ==
        "Conversation based learning"
    )
