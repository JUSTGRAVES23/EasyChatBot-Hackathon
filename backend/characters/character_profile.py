"""
Character Profile Model.

Defines AI companion identity.

Characters are separate from agents.

Character:
- personality
- communication style
- learning approach
- artwork availability
- selection availability

Agent:
- execution capability
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterProfile:
    """
    Defines an EasyChatBot AI companion.

    A character can only be offered for learner selection
    when its EasyChatBot artwork has been approved.

    The character profile therefore contains both:

    - identity / behavioural information;
    - presentation readiness information.
    """

    character_id: str

    name: str

    description: str

    personality: str

    learning_style: str

    artwork_available: bool = False

    artwork_status: str = "not_available"

    selectable: bool = False