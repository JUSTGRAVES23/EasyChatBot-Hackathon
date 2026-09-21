from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from app.domain.learning_assessment.learner_skill_state import LearnerSkillState
from app.domain.learning_assessment.reinforcement_decision import ReinforcementDecision, ReinforcementPriority

@dataclass(frozen=True, slots=True)
class LearnerSkillStateUpdate:
    state: LearnerSkillState
    decision: ReinforcementDecision

class LearnerSkillStateService:
    """Deterministically updates skill evidence; persistence stays outside."""

    def apply_outcome(self, *, current: LearnerSkillState | None, learner_id: str,
                      world_id: str, skill_id: str, correct: bool, now: datetime) -> LearnerSkillStateUpdate:
        if not isinstance(correct, bool):
            raise ValueError("correct must be a boolean.")
        if current is not None:
            if current.learner_id != learner_id: raise ValueError("Learner mismatch.")
            if current.world_id != world_id: raise ValueError("World mismatch.")
            if current.skill_id != skill_id: raise ValueError("Skill mismatch.")

        attempts = (current.attempt_count if current else 0) + 1
        correct_count = (current.correct_count if current else 0) + (1 if correct else 0)
        incorrect_count = (current.incorrect_count if current else 0) + (0 if correct else 1)
        failure_streak = 0 if correct else (current.failure_streak if current else 0) + 1
        success_streak = (current.success_streak if current else 0) + 1 if correct else 0
        last_failure = current.last_failure_at if current else None
        last_success = current.last_success_at if current else None
        if correct: last_success = now
        else: last_failure = now

        if failure_streak >= 2:
            priority, reason, required = ReinforcementPriority.HIGH, "repeated_failure", True
        elif incorrect_count >= 1:
            priority, reason, required = ReinforcementPriority.MEDIUM, "recent_failure", True
        else:
            priority, reason, required = ReinforcementPriority.NONE, "no_recorded_failure", False

        state = LearnerSkillState(
            learner_id=learner_id, world_id=world_id, skill_id=skill_id,
            attempt_count=attempts, correct_count=correct_count, incorrect_count=incorrect_count,
            failure_streak=failure_streak, success_streak=success_streak,
            last_attempt_at=now, last_failure_at=last_failure, last_success_at=last_success,
            reinforcement_required=required,
        )
        decision = ReinforcementDecision(
            skill_id=skill_id, priority=priority, reason=reason,
            recommended_repetition=required,
        )
        return LearnerSkillStateUpdate(state=state, decision=decision)
