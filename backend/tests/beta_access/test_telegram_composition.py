from __future__ import annotations

from backend.application.telegram_bootstrap import (
    create_telegram_runtime,
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

    reset_telegram_runtime()

    runtime = create_telegram_runtime()

    assert runtime is not None

    reset_telegram_runtime()