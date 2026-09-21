from __future__ import annotations

from abc import ABC, abstractmethod

from .assessment_attempt import AssessmentAttempt
from .learning_event import LearningEvent
from .learner_skill_state import LearnerSkillState
from .question import AssessmentQuestion


class AssessmentQuestionRepository(ABC):
    @abstractmethod
    async def get(self, *, question_id: str) -> AssessmentQuestion | None: ...


class AssessmentAttemptRepository(ABC):
    @abstractmethod
    async def save(self, attempt: AssessmentAttempt) -> AssessmentAttempt: ...

    @abstractmethod
    async def get_recent_for_skill(
        self, *, learner_id: str, world_id: str, skill_id: str, limit: int = 20
    ) -> list[AssessmentAttempt]: ...


class LearningEventRepository(ABC):
    @abstractmethod
    async def save(self, event: LearningEvent) -> LearningEvent: ...

    @abstractmethod
    async def count_recent_failures(
        self, *, learner_id: str, world_id: str, skill_id: str, limit: int = 20
    ) -> int: ...


class LearnerSkillStateRepository(ABC):
    """Persistence port for the current learner/World/skill projection."""

    @abstractmethod
    def get(
        self, *, learner_id: str, world_id: str, skill_id: str
    ) -> LearnerSkillState | None: ...

    @abstractmethod
    def save(self, state: LearnerSkillState) -> LearnerSkillState: ...
