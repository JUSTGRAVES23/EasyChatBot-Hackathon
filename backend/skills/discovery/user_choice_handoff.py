"""
Discovery User Choice & Controlled Handoff Skill.

Presents verified recommendations and converts an explicit
learner choice into a controlled handoff request.

The Skill establishes the human decision boundary.

It does not:

- perform discovery
- call external providers
- call LLMs
- automatically select a recommendation for the learner
- execute external actions
- persist memory
- modify learner preferences
- bypass Runtime controls

Architecture:

Verified Recommendations
        |
        v
User Choice & Controlled Handoff
        |
        +--> Awaiting learner choice
        |
        v
Explicit learner selection
        |
        v
Controlled Handoff
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.skills.discovery.personalised_content_adaptation import (
    PersonalisedRecommendation,
)
from backend.skills.discovery.discovery_quality_verification import (
    VerifiedRecommendation,
)
from backend.skills.skill import (
    Skill,
    SkillInput,
)
from backend.skills.skill_result import (
    SkillResult,
)


@dataclass(frozen=True)
class HandoffOption:
    """
    Recommendation option presented to the learner.
    """

    option_id: str
    rank: int
    recommendation: PersonalisedRecommendation

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation."""

        return {
            "option_id": self.option_id,
            "rank": self.rank,
            "recommendation": (
                self.recommendation.as_dict()
            ),
        }


@dataclass(frozen=True)
class ControlledHandoff:
    """
    Explicit learner-approved handoff.

    A handoff is created only after the learner provides
    a valid option identifier.
    """

    option_id: str
    rank: int
    recommendation: PersonalisedRecommendation

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation."""

        return {
            "option_id": self.option_id,
            "rank": self.rank,
            "recommendation": (
                self.recommendation.as_dict()
            ),
        }


class UserChoiceControlledHandoffSkill(Skill):
    """
    Present verified recommendations and process explicit
    learner selection.

    Expected metadata:

        {
            "verified_recommendations": [
                VerifiedRecommendation(...),
                ...
            ],

            "selected_option_id": "recommendation-1"
        }

    If selected_option_id is absent, the Skill returns the
    available options and an awaiting-choice state.

    The Skill never automatically selects an option.
    """

    skill_id = "discovery.user_choice_handoff"
    name = "User Choice and Controlled Handoff"
    version = "1.0.0"

    @staticmethod
    def _option_id(rank: int) -> str:
        """Create a stable option identifier."""

        return f"recommendation-{rank}"

    async def execute(
        self,
        skill_input: SkillInput,
    ) -> SkillResult:
        """
        Present verified recommendations or process an
        explicit learner selection.
        """

        if skill_input is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="Skill input cannot be None.",
            )

        raw_recommendations = (
            skill_input.metadata.get(
                "verified_recommendations"
            )
        )

        if raw_recommendations is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "verified_recommendations are required."
                ),
            )

        if not isinstance(
            raw_recommendations,
            (list, tuple),
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "verified_recommendations must be "
                    "a list or tuple."
                ),
            )

        options: list[HandoffOption] = []

        for item in raw_recommendations:
            if not isinstance(
                item,
                VerifiedRecommendation,
            ):
                continue

            recommendation = item.recommendation

            options.append(
                HandoffOption(
                    option_id=self._option_id(
                        recommendation
                        .recommendation
                        .recommendation
                        .rank
                    ),
                    rank=(
                        recommendation
                        .recommendation
                        .recommendation
                        .rank
                    ),
                    recommendation=recommendation,
                )
            )

        selected_option_id = (
            skill_input.metadata.get(
                "selected_option_id"
            )
        )

        # -------------------------------------------------
        # Human decision boundary
        #
        # No selection means the learner must choose.
        # -------------------------------------------------

        if selected_option_id is None:
            return SkillResult.succeeded(
                skill_id=self.skill_id,
                output={
                    "status": "awaiting_user_choice",
                    "options": options,
                    "handoff": None,
                },
            )

        if not isinstance(
            selected_option_id,
            str,
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "selected_option_id must be a string."
                ),
            )

        selected_option_id = (
            selected_option_id.strip()
        )

        if not selected_option_id:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "selected_option_id cannot be empty."
                ),
            )

        selected = next(
            (
                option
                for option in options
                if option.option_id
                == selected_option_id
            ),
            None,
        )

        if selected is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "Selected recommendation does not "
                    "exist in the verified options."
                ),
            )

        handoff = ControlledHandoff(
            option_id=selected.option_id,
            rank=selected.rank,
            recommendation=selected.recommendation,
        )

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output={
                "status": "handoff_approved",
                "options": options,
                "handoff": handoff,
            },
        )