from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TeacherMemory:
    """
    Validated teaching observation.

    Contains only educational information.
    """

    memory_id: str
    learner_hash: str
    category: str
    observation: str
    confidence: float
    created_at: datetime
    last_validated_at: datetime
