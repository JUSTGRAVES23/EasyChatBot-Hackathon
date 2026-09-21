from datetime import datetime, timezone
import pytest
from app.domain.learning_assessment.assessment_attempt import AssessmentAttempt, AssessmentOutcome
from app.domain.learning_assessment.learning_event import LearningEvent, LearningEventOutcome
from app.domain.learning_assessment.question import AssessmentQuestion, QuestionType

def now(): return datetime.now(timezone.utc)

def test_question_is_immutable_and_valid():
    q = AssessmentQuestion("q1","french","past-tense","J'___ au marché.","suis allé",QuestionType.TEXT)
    assert q.question_id == "q1"
    with pytest.raises((AttributeError, TypeError)): q.prompt = "changed"

@pytest.mark.parametrize("field", ["question_id","world_id","skill_id","prompt","expected_answer"])
def test_question_rejects_empty_required_fields(field):
    values = dict(question_id="q1", world_id="french", skill_id="past-tense",
                  prompt="Question", expected_answer="answer")
    values[field] = " "
    with pytest.raises(ValueError): AssessmentQuestion(**values)

def test_question_rejects_invalid_difficulty():
    with pytest.raises(ValueError):
        AssessmentQuestion("q1","french","grammar","Q","A",difficulty=6)

def test_attempt_rejects_invalid_score():
    with pytest.raises(ValueError):
        AssessmentAttempt("a1","learner-1","french","q1","A",
                          AssessmentOutcome.CORRECT,2,now())

def test_learning_event_requires_skill():
    with pytest.raises(ValueError):
        LearningEvent("e1","learner-1","french","q1"," ",
                      LearningEventOutcome.INCORRECT,now())
