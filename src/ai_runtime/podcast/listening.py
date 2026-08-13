"""
Provider-independent Podcast Listening Proposal contracts.

This module defines the domain representation for proposing
a podcast listening action to a learner.

Architecture:

PodcastRecommendation
        |
        v
ListeningProposal
        |
        v
Application / UI
        |
        v
Learner decision

The proposal is intentionally passive.

It does not:

- start playback;
- control an audio player;
- call Apple;
- call Spotify;
- access a learner's external account;
- subscribe the learner;
- purchase content;
- modify external systems;
- perform autonomous actions.

The learner must explicitly decide whether to continue.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ListeningProposalAction(StrEnum):
    """
    Actions that may be presented to the learner.

    The Runtime only proposes these actions. It does not
    execute them.
    """

    LISTEN = "listen"
    OPEN = "open"


@dataclass(frozen=True, slots=True)
class ListeningProposal:
    """
    Provider-independent proposal for a podcast listening action.

    Attributes:
        user_id:
            Learner receiving the proposal.

        podcast_id:
            External podcast identifier.

        podcast_title:
            Human-readable podcast title.

        podcast_url:
            Verified podcast URL.

        character_id:
            Character presenting the proposal.

        character_name:
            Human-readable character name.

        message:
            Character-facing proposal message.

        action:
            Proposed learner action.

        reason:
            Explanation of why the podcast is being proposed.

        target_language:
            Language associated with the learning experience.

        learner_level:
            Learner level associated with the recommendation.
    """

    user_id: str
    podcast_id: str
    podcast_title: str
    podcast_url: str
    character_id: str
    character_name: str
    message: str
    action: ListeningProposalAction
    reason: str
    target_language: str
    learner_level: str

    def __post_init__(self) -> None:
        values = {
            "user_id": self.user_id,
            "podcast_id": self.podcast_id,
            "podcast_title": self.podcast_title,
            "podcast_url": self.podcast_url,
            "character_id": self.character_id,
            "character_name": self.character_name,
            "message": self.message,
            "reason": self.reason,
            "target_language": self.target_language,
            "learner_level": self.learner_level,
        }

        for name, value in values.items():
            if not isinstance(value, str):
                raise ValueError(
                    f"ListeningProposal {name} must be a string."
                )

            if not value.strip():
                raise ValueError(
                    f"ListeningProposal {name} cannot be empty."
                )

        if not self.podcast_url.startswith(
            (
                "http://",
                "https://",
            )
        ):
            raise ValueError(
                "ListeningProposal podcast_url must use "
                "HTTP or HTTPS."
            )

    @property
    def is_passive(self) -> bool:
        """
        Return True because this object represents a proposal only.

        Creating a ListeningProposal never causes playback or
        another external side effect.
        """

        return True