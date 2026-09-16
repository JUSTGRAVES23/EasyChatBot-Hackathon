from __future__ import annotations

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

    assert config.scheduler_enabled is False
    assert config.first_run_enabled is False
    assert config.activation_allowed is False


def test_scheduler_requires_explicit_activation(
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

    assert config.scheduler_enabled is True
    assert config.first_run_enabled is False
    assert config.activation_allowed is False


def test_first_run_requires_scheduler_activation(
    monkeypatch,
):
    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
        "false",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_FIRST_RUN_ENABLED",
        "true",
    )

    config = AcademyActivationConfig.from_environment()

    assert config.scheduler_enabled is False
    assert config.first_run_enabled is True
    assert config.activation_allowed is False


def test_explicit_activation_requires_both_switches(
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

    assert config.scheduler_enabled is True
    assert config.first_run_enabled is True
    assert config.activation_allowed is True


@pytest.mark.parametrize(
    "value",
    [
        "invalid",
        "maybe",
        "enabled",
    ],
)
def test_invalid_activation_value_fails_closed(
    monkeypatch,
    value,
):
    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
        value,
    )

    with pytest.raises(
        RuntimeError,
        match="EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
    ):
        AcademyActivationConfig.from_environment()

