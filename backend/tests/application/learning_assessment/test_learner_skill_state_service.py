from datetime import datetime, timezone
import pytest
from app.application.learning_assessment.learner_skill_state_service import LearnerSkillStateService
from app.domain.learning_assessment.reinforcement_decision import ReinforcementPriority

NOW = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
S = LearnerSkillStateService()

def apply(current, correct, skill="french.prepositions"):
    return S.apply_outcome(current=current, learner_id="learner-1", world_id="french_world",
                            skill_id=skill, correct=correct, now=NOW)

def test_first_correct_has_no_reinforcement():
    r = S.apply_outcome(current=None, learner_id="learner-1", world_id="french_world",
                        skill_id="french.articles", correct=True, now=NOW)
    assert r.state.attempt_count == 1
    assert r.state.correct_count == 1
    assert r.state.failure_streak == 0
    assert r.state.success_streak == 1
    assert r.decision.priority is ReinforcementPriority.NONE

def test_first_failure_is_medium():
    r = apply(None, False)
    assert r.state.incorrect_count == 1
    assert r.state.failure_streak == 1
    assert r.decision.priority is ReinforcementPriority.MEDIUM

def test_repeated_failure_is_high():
    r1 = apply(None, False)
    r2 = apply(r1.state, False)
    assert r2.state.failure_streak == 2
    assert r2.decision.priority is ReinforcementPriority.HIGH

def test_success_resets_failure_streak_but_history_remains():
    r1 = apply(None, False)
    r2 = apply(r1.state, True)
    assert r2.state.failure_streak == 0
    assert r2.state.success_streak == 1
    assert r2.state.incorrect_count == 1
    assert r2.state.reinforcement_required is True

def test_learner_boundary():
    r = apply(None, False)
    with pytest.raises(ValueError, match="Learner mismatch"):
        S.apply_outcome(current=r.state, learner_id="learner-2", world_id="french_world",
                        skill_id="french.prepositions", correct=True, now=NOW)

def test_world_boundary():
    r = apply(None, False)
    with pytest.raises(ValueError, match="World mismatch"):
        S.apply_outcome(current=r.state, learner_id="learner-1", world_id="spanish_world",
                        skill_id="french.prepositions", correct=True, now=NOW)

def test_skill_boundary():
    r = apply(None, False)
    with pytest.raises(ValueError, match="Skill mismatch"):
        S.apply_outcome(current=r.state, learner_id="learner-1", world_id="french_world",
                        skill_id="french.articles", correct=True, now=NOW)
