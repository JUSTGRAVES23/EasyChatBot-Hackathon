from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.questionnaire_runtime as questionnaire_runtime_api


class FakeRuntime:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.command = None

    async def submit_answer(self, *, command):
        self.command = command

        if self.error is not None:
            raise self.error

        return self.result


class FakeAttempt:
    attempt_id = "attempt-001"
    question_id = "question-001"
    world_id = "world-001"
    score = 1.0


class FakeState:
    reinforcement_required = False


class FakeDecision:
    class Priority:
        value = "none"

    priority = Priority()


class FakeResult:
    attempt = FakeAttempt()
    learner_skill_state = FakeState()
    reinforcement_decision = FakeDecision()


def build_app(
    runtime: FakeRuntime,
    principal_user_id: str = "server-user-001",
) -> FastAPI:
    """
    Build an isolated FastAPI application for the questionnaire runtime API.

    The production route uses get_current_principal. The test replaces that
    exact dependency object through FastAPI's supported dependency override
    mechanism.

    This prevents the production authentication dependency from attempting
    to access request.app.state.auth_repository in this isolated unit/API
    test application.
    """
    app = FastAPI()

    async def fake_principal():
        return SimpleNamespace(
            user_id=principal_user_id,
            is_active=True,
        )

    # IMPORTANT:
    # Use the exact get_current_principal object imported by the production
    # questionnaire runtime module. This is the dependency object captured
    # by Depends(...) when the route was defined.
    app.dependency_overrides[
        questionnaire_runtime_api.get_current_principal
    ] = fake_principal

    app.include_router(
        questionnaire_runtime_api.create_questionnaire_runtime_router(
            runtime=runtime,
        )
    )

    return app


def test_authenticated_answer_uses_server_principal_not_client_learner_id():
    runtime = FakeRuntime(result=FakeResult())
    app = build_app(runtime)

    try:
        client = TestClient(app)

        response = client.post(
            "/api/academy/questionnaires/answers",
            json={
                "world_id": "world-001",
                "question_id": "question-001",
                "answer": "bonjour",
                "learner_id": "attacker-supplied-user",
            },
        )

        # learner_id is deliberately NOT part of the public request
        # contract. The production request model uses extra="forbid".
        #
        # Therefore the correct security result is 422 rather than 200.
        assert response.status_code == 422

        # The request must be rejected before the runtime is called.
        assert runtime.command is None

    finally:
        app.dependency_overrides.clear()


def test_runtime_rejects_unknown_question_as_not_found():
    runtime = FakeRuntime(
        error=ValueError(
            "Assessment question not found."
        )
    )

    app = build_app(runtime)

    try:
        client = TestClient(app)

        response = client.post(
            "/api/academy/questionnaires/answers",
            json={
                "world_id": "world-001",
                "question_id": "missing",
                "answer": "bonjour",
            },
        )

        assert response.status_code == 404

        assert response.json() == {
            "detail": "Assessment question not found."
        }

        # Verify the learner identity came from the server-side principal.
        assert runtime.command is not None
        assert runtime.command.learner_id == "server-user-001"

        assert runtime.command.world_id == "world-001"
        assert runtime.command.question_id == "missing"
        assert runtime.command.answer == "bonjour"

    finally:
        app.dependency_overrides.clear()


def test_runtime_rejects_question_from_other_world():
    runtime = FakeRuntime(
        error=ValueError(
            "Assessment question does not belong to the requested world."
        )
    )

    app = build_app(runtime)

    try:
        client = TestClient(app)

        response = client.post(
            "/api/academy/questionnaires/answers",
            json={
                "world_id": "wrong-world",
                "question_id": "question-001",
                "answer": "bonjour",
            },
        )

        assert response.status_code == 400

        assert response.json() == {
            "detail": (
                "Assessment question does not belong "
                "to the requested world."
            )
        }

        # Authentication must still resolve to the server-side principal.
        assert runtime.command is not None
        assert runtime.command.learner_id == "server-user-001"

        assert runtime.command.world_id == "wrong-world"
        assert runtime.command.question_id == "question-001"
        assert runtime.command.answer == "bonjour"

    finally:
        app.dependency_overrides.clear()


def test_runtime_rejects_extra_client_fields():
    runtime = FakeRuntime(result=FakeResult())
    app = build_app(runtime)

    try:
        client = TestClient(app)

        response = client.post(
            "/api/academy/questionnaires/answers",
            json={
                "world_id": "world-001",
                "question_id": "question-001",
                "answer": "bonjour",
                "learner_id": "should-not-be-accepted",
            },
        )

        # Security contract:
        # QuestionnaireAnswerRequest uses extra="forbid".
        #
        # A client must never be able to provide learner identity.
        assert response.status_code == 422

        # The runtime must not execute an invalid request.
        assert runtime.command is None

    finally:
        app.dependency_overrides.clear()