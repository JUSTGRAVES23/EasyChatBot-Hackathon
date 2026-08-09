"""
Character Profile Model.

Defines AI companion identity.

Characters are separate from agents.

Character:
- personality
- communication style
- learning approach

Agent:
- execution capability
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterProfile:
    """
    Defines an EasyChatBot AI companion.
    """

    character_id: str

    name: str

    description: str

    personality: str

    learning_style: str