"""
EasyChatBot Character Registry.

The registry provides the approved characters available
to the application.

Characters define identity and behaviour.

Agents remain responsible for capabilities and execution.
"""

from backend.characters.character_profile import (
    CharacterProfile,
)


class CharacterRegistry:
    """
    Registry of approved EasyChatBot AI companions.
    """

    def __init__(self) -> None:
        self._characters = {
            "yeti": CharacterProfile(
                character_id="yeti",
                name="Yeti",
                description=(
                    "A friendly AI companion who helps "
                    "you discover knowledge and practice languages."
                ),
                personality=(
                    "Curious, encouraging and supportive."
                ),
                learning_style=(
                    "Conversation based learning."
                ),
            ),
            "clara": CharacterProfile(
                character_id="clara",
                name="Clara",
                description=(
                    "A professional learning companion "
                    "focused on technology and career topics."
                ),
                personality=(
                    "Analytical, structured and supportive."
                ),
                learning_style=(
                    "Structured and practical learning."
                ),
            ),
            "luminate": CharacterProfile(
                character_id="luminate",
                name="Luminate",
                description=(
                    "A creative companion for culture, "
                    "ideas and exploration."
                ),
                personality=(
                    "Creative, inspiring and curious."
                ),
                learning_style=(
                    "Exploration and discussion."
                ),
            ),
        }

    def get(
        self,
        character_id: str,
    ) -> CharacterProfile:
        """
        Return an approved character.

        Raises:
            ValueError:
                If the character does not exist.
        """

        normalized_id = character_id.strip().lower()

        try:
            return self._characters[normalized_id]
        except KeyError as exc:
            raise ValueError(
                f"Unknown character: {character_id}"
            ) from exc

    def list_characters(
        self,
    ) -> list[CharacterProfile]:
        """
        Return all approved characters.
        """

        return list(self._characters.values())