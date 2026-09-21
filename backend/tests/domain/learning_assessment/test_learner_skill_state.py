from datetime import datetime, timezone
import pytest
from app.domain.learning_assessment.learner_skill_state import LearnerSkillState
from app.domain.learning_assessment.reinforcement_decision import ReinforcementDecision, ReinforcementPriority

NOW = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)

def state(**overrides):
    v = dict(learner_id="learner-1", world_id="french_world", skill_id="french.prepositions",
             attempt_count=2, correct_count=1, incorrect_count=1, failure_streak=1, success_streak=0,
             last_attempt_at=NOW, last_failure_at=NOW,
             last_success_at=datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc),
             reinforcement_required=True)
    v.update(overrides)
    return LearnerSkillState(**v)

def test_state_is_immutable():
    with pytest.raises((AttributeError, TypeError)):
        state().failure_streak = 3

def test_attempts_equal_outcomes():
    with pytest.raises(ValueError): state(attempt_count=3)

def test_failure_streak_cannot_exceed_failures():
    with pytest.raises(ValueError): state(failure_streak=2)

def test_success_streak_cannot_exceed_successes():
    with pytest.raises(ValueError): state(success_streak=2)

def test_failure_timestamp_cannot_be_after_attempt():
    with pytest.raises(ValueError):
        state(last_failure_at=datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc))

def test_decision_requires_enum():
    with pytest.raises(ValueError):
        ReinforcementDecision("skill", "HIGH", "reason", True)

def test_decision_is_immutable():
    d = ReinforcementDecision("skill", ReinforcementPriority.HIGH, "reason", True)
    with pytest.raises((AttributeError, TypeError)): d.priority = ReinforcementPriority.NONE
