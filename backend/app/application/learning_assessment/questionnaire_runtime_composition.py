from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.application.learning_assessment.assessment_service import (
    AssessmentService,
)
from app.application.learning_assessment.learner_skill_state_service import (
    LearnerSkillStateService,
)
from app.application.learning_assessment.questionnaire_runtime import (
    QuestionnaireRuntime,
)
from app.infrastructure.persistence.postgresql_learner_skill_state_repository import (
    PostgreSQLLearnerSkillStateRepository,
)
from app.infrastructure.persistence.postgresql_learning_assessment_repositories import (
    PostgreSQLAssessmentAttemptRepository,
    PostgreSQLAssessmentQuestionRepository,
    PostgreSQLLearningEventRepository,
)


def create_questionnaire_runtime(
    *,
    session_factory: sessionmaker[Session],
) -> QuestionnaireRuntime:
    """Compose the production questionnaire runtime from existing boundaries.

    The runtime deliberately reuses the existing synchronous persistence
    session factory and AssessmentService. No second engine or persistence
    boundary is created here.
    """
    if session_factory is None:
        raise ValueError("session_factory is required.")

    question_repository = PostgreSQLAssessmentQuestionRepository(
        session_factory
    )
    attempt_repository = PostgreSQLAssessmentAttemptRepository(
        session_factory
    )
    learning_event_repository = PostgreSQLLearningEventRepository(
        session_factory
    )
    skill_state_repository = PostgreSQLLearnerSkillStateRepository(
        session_factory
    )

    assessment_service = AssessmentService(
        questions=question_repository,
        attempts=attempt_repository,
        events=learning_event_repository,
        skill_states=skill_state_repository,
        skill_state_service=LearnerSkillStateService(),
    )

    return QuestionnaireRuntime(
        assessment_service=assessment_service,
    )


__all__ = ["create_questionnaire_runtime"]
