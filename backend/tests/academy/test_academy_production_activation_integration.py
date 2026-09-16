from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.application.academy.academy_activation import (
    AcademyActivationConfig,
)


pytestmark = pytest.mark.integration


def test_academy_activation_is_disabled_by_default(
    monkeypatch,
):
    monkeypatch.delenv(
        "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
        raising=False,
    )

    monkeypatch.delenv(
        "EASYCHATBOT_ACADEMY_FIRST_RUN_ENABLED",
        raising=False,
    )

    config = AcademyActivationConfig.from_environment()

    assert config.activation_allowed is False


def test_academy_activation_requires_both_flags(
    monkeypatch,
):
    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_FIRST_RUN_ENABLED",
        "false",
    )

    config = AcademyActivationConfig.from_environment()

    assert config.activation_allowed is False


def test_academy_activation_can_be_explicitly_enabled(
    monkeypatch,
):
    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_FIRST_RUN_ENABLED",
        "true",
    )

    config = AcademyActivationConfig.from_environment()

    assert config.activation_allowed is True


def test_disabled_academy_does_not_create_workflow(
    monkeypatch,
):
    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
        "false",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_FIRST_RUN_ENABLED",
        "false",
    )

    config = AcademyActivationConfig.from_environment()

    with patch(
        "backend.app.main.create_academy_one_week_workflow"
    ) as academy_factory:

        if config.activation_allowed:
            academy_factory()

        academy_factory.assert_not_called()


def test_enabled_academy_uses_existing_boundaries(
    monkeypatch,
):
    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_FIRST_RUN_ENABLED",
        "true",
    )

    config = AcademyActivationConfig.from_environment()

    assert config.activation_allowed is True

    existing_session_factory = MagicMock(
        name="existing_session_factory",
    )

    existing_telegram_client = MagicMock(
        name="existing_announcement_telegram_client",
    )

    with patch(
        "backend.app.main.create_academy_one_week_workflow"
    ) as academy_factory:

        if config.activation_allowed:
            academy_factory(
                session_factory=existing_session_factory,
                telegram_bot=existing_telegram_client,
            )

        academy_factory.assert_called_once_with(
            session_factory=existing_session_factory,
            telegram_bot=existing_telegram_client,
        )
