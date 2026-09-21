from __future__ import annotations

from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from tests.application.composition.deterministic_language_detector import (
    DeterministicLanguageDetector,
)
from application.telegram_bootstrap import (
    create_telegram_runtime,
    get_telegram_production_composition,
    reset_telegram_runtime,
)


class FakeConversationRuntime:
    """
    Test double.

    Telegram composition tests should not create
    real LLM providers.
    """

    async def respond(
        self,
        *args,
        **kwargs,
    ):
        return "test response"


class FakeFunctionalityControlAuthorizer:
    """Allow the deterministic test control service to be constructed."""

    def can_control_functionality(
        self,
        *,
        actor,
        environment,
        functionality_id,
    ):
        return True


class FakeFunctionalityControlRepository:
    """
    Deterministic repository double.

    Production uses PostgreSQLFunctionalityControlRepository.
    """

    def get_availability(
        self,
        *,
        environment,
        functionality_id,
    ):
        return "enabled"

    def get_last_action(
        self,
        *,
        environment,
        functionality_id,
    ):
        return None

    def record_transition(self, **kwargs):
        raise AssertionError(
            "Composition test must not perform a control transition."
        )


def make_functionality_control_service():
    return FunctionalityOperationalControlService(
        authorizer=FakeFunctionalityControlAuthorizer(),
        repository=FakeFunctionalityControlRepository(),
    )


def test_telegram_runtime_composition_creates_runtime(
    monkeypatch,
):
    #
    # Test-only privacy configuration.
    #
    # Never use this value as a production secret.
    #
    monkeypatch.setenv(
        "PRIVACY_HASH_SECRET",
        "test-only-telegram-composition-secret",
    )

    #
    # Database dependency isolation.
    #

    class FakeEngine:
        pass

    class FakeSessionFactory:
        pass

    monkeypatch.setattr(
        "backend.application.telegram_bootstrap.create_database_engine",
        lambda: FakeEngine(),
    )

    monkeypatch.setattr(
        "backend.application.telegram_bootstrap.create_session_factory",
        lambda engine: FakeSessionFactory(),
    )

    #
    # AI runtime isolation.
    #

    monkeypatch.setattr(
        "backend.application.telegram_bootstrap.create_conversation_runtime",
        lambda: FakeConversationRuntime(),
    )

    #
    # Functionality-control isolation.
    #
    # The production composition requires this dependency explicitly.
    # The test supplies a deterministic repository-backed service rather
    # than weakening the production contract.
    #

    functionality_control_service = (
        make_functionality_control_service()
    )

    reset_telegram_runtime()

    try:
        runtime = create_telegram_runtime(
            functionality_control_service=(
                functionality_control_service
            ),
            language_detector=DeterministicLanguageDetector(),
        )

        assert runtime is not None

        composition = get_telegram_production_composition()

        assert composition is not None
        assert composition.conversation_boundary is not None

    finally:
        reset_telegram_runtime()
