from __future__ import annotations


from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class MemoryCandidate:
    """
    Temporary educational memory proposal.

    Compatibility boundary between:

    Beta memory workflow
        +
    Future domain MemoryItem model.


    Not persisted.
    """

    candidate_id: str

    learner_id: str | None = None

    memory_type: str | None = None

    content: str | None = None

    confidence_score: float | None = None

    source_event_id: str | None = None

    metadata: dict[str, Any] | None = None

    created_at: datetime | None = None


    # -------------------------------------------------
    # Backward compatibility fields
    # -------------------------------------------------

    learner_hash: str | None = None

    category: str | None = None

    observation: str | None = None

    confidence: float | None = None

    evidence_event_ids: list[str] | None = None



    def normalized_memory_type(self) -> str:
        """
        Returns unified memory type.
        """

        return (
            self.memory_type
            or self.category
            or ""
        )



    def normalized_content(self) -> str:
        """
        Returns unified content.
        """

        return (
            self.content
            or self.observation
            or ""
        )



    def normalized_confidence(self) -> float:
        """
        Returns unified confidence.
        """

        return (
            self.confidence_score
            if self.confidence_score is not None
            else self.confidence
            or 0.0
        )



    def normalized_learner_id(self) -> str:
        """
        Returns learner identifier.

        Future:
        this becomes learner_id only.
        """

        return (
            self.learner_id
            or self.learner_hash
            or ""
        )



    def normalized_source_events(self) -> list[str]:
        """
        Returns evidence events.
        """

        if self.evidence_event_ids:
            return self.evidence_event_ids

        if self.source_event_id:
            return [self.source_event_id]

        return []