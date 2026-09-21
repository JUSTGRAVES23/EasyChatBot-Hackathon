from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.domain.learning_assessment.learner_error_candidate import (
    LearnerErrorCandidate,
)
from app.domain.learning_assessment.learning_observation import (
    LearningObservationCandidate,
)


@dataclass(frozen=True, slots=True)
class CharacterLearningAnalysis:
    """Provider-independent result of analysing one learner turn."""

    observations: tuple[LearningObservationCandidate, ...] = ()
    learner_errors: tuple[LearnerErrorCandidate, ...] = ()

    def __post_init__(self) -> None:
        observation_ids = {
            observation.observation_id for observation in self.observations
        }
        error_ids = {
            error.observation.observation_id for error in self.learner_errors
        }

        if len(observation_ids) != len(self.observations):
            raise ValueError("Duplicate observation_id values are not allowed.")

        if not error_ids.issubset(observation_ids):
            raise ValueError(
                "Every learner error must reference an observation in the analysis."
            )


class CharacterLearningAnalyzer(Protocol):
    """Analysis boundary.

    Implementations analyse input but MUST NOT persist evidence, mutate learner
    skill state, call repositories, or perform autonomous side effects.
    """

    async def analyze(
        self,
        *,
        learner_id: str,
        world_id: str,
        skill_id: str,
        observation_id_prefix: str,
        learner_text: str,
        character_response: str | None,
        context: dict[str, object] | None = None,
    ) -> CharacterLearningAnalysis:
        """Return candidates only; stable IDs derive from the source turn."""
        ...
