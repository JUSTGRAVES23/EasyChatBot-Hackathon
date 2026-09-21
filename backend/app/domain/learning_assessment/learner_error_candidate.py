from __future__ import annotations

from dataclasses import dataclass

from app.domain.learning_assessment.learning_evidence import (
    LearningEvidenceStatus,
)
from app.domain.learning_assessment.learning_observation import (
    LearningObservationCandidate,
)


@dataclass(frozen=True, slots=True)
class LearnerErrorCandidate:
    """A learner-improvement candidate derived from an observation.

    It deliberately contains no persistence or skill-state behaviour.
    """

    observation: LearningObservationCandidate

    def __post_init__(self) -> None:
        if self.observation.status is not LearningEvidenceStatus.CONFIRMED_ERROR:
            raise ValueError(
                "Learner error candidates must have CONFIRMED_ERROR status."
            )
        if self.observation.learner_text is None:
            raise ValueError("Learner error candidates require learner_text.")
