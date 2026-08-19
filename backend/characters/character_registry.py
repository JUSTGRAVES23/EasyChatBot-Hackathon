"""
EasyChatBot Character Registry.

The registry provides the approved characters available
to the application.

Characters define identity and behaviour.

Agents remain responsible for capabilities and execution.

Character selection readiness is determined by artwork
availability.

A character without approved EasyChatBot artwork is not
selectable from the character selection experience.
"""

from backend.characters.character_profile import (
    CharacterProfile,
)


class CharacterRegistry:
    """
    Registry of approved EasyChatBot AI companions.

    Character identity and behaviour belong here.

    Artwork readiness also belongs to the character profile
    because artwork availability determines whether the
    character may be offered for selection.
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
                artwork_available=True,
                artwork_status="approved",
                selectable=True,
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
                artwork_available=True,
                artwork_status="approved",
                selectable=True,
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
                artwork_available=True,
                artwork_status="approved",
                selectable=True,
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

        normalized_id = (
            character_id.strip().lower()
        )

        try:

            return self._characters[
                normalized_id
            ]

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

        return list(
            self._characters.values()
        )

    def list_selectable_characters(
        self,
    ) -> list[CharacterProfile]:
        """
        Return characters that are currently available
        for learner selection.

        Selection requires:

        - approved artwork;
        - artwork_available=True;
        - selectable=True.
        """

        return [
            character
            for character in self._characters.values()
            if (
                character.artwork_available
                and character.artwork_status == "approved"
                and character.selectable
            )
        ]