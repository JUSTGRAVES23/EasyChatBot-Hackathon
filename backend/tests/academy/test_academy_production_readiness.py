from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from app.application.academy.academy_one_week_workflow import (
    AcademyOneWeekWorkflow,
)
from app.application.composition.academy_production import (
    create_academy_one_week_workflow,
)
from cybersecurity.email.email_provider_manager import (
    EmailProviderManager,
)


pytestmark = pytest.mark.integration


def test_production_configuration_is_explicitly_available(
    monkeypatch,
):
    """
    Verify the required Academy production configuration can be
    supplied explicitly.

    This test does not activate production delivery.
    """

    monkeypatch.setenv(
        "EASYCHATBOT_PORTAL_URL",
        "https://academy.example.com",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_REGISTRATION_EMAIL",
        "academy@example.com",
    )

    assert (
        os.getenv("EASYCHATBOT_PORTAL_URL")
        == "https://academy.example.com"
    )

    assert (
        os.getenv("EASYCHATBOT_REGISTRATION_EMAIL")
        == "academy@example.com"
    )


def test_production_configuration_composes_academy_workflow(
    monkeypatch,
):
    """
    Verify production configuration is sufficient to construct the
    Academy workflow.

    Infrastructure is injected so this test does not create a real
    database connection or external delivery client.
    """

    monkeypatch.setenv(
        "EASYCHATBOT_PORTAL_URL",
        "https://academy.example.com",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_REGISTRATION_EMAIL",
        "academy@example.com",
    )

    session_factory = MagicMock(
        name="production_session_factory",
    )

    provider_manager = MagicMock(
        spec=EmailProviderManager,
        name="production_email_provider_manager",
    )

    workflow = create_academy_one_week_workflow(
        session_factory=session_factory,
        email_provider_manager=provider_manager,
    )

    assert isinstance(
        workflow,
        AcademyOneWeekWorkflow,
    )

    assert (
        workflow._users._session_factory
        is session_factory
    )

    assert (
        workflow._deliveries._session_factory
        is session_factory
    )

    assert (
        workflow._notifications
        ._registration_email
        == "academy@example.com"
    )

    assert (
        workflow._notifications
        ._portal_url
        == "https://academy.example.com"
    )


def test_missing_production_portal_configuration_blocks_composition(
    monkeypatch,
):
    """
    Production composition must fail closed when the portal URL is
    absent.
    """

    monkeypatch.delenv(
        "EASYCHATBOT_PORTAL_URL",
        raising=False,
    )

    monkeypatch.setenv(
        "EASYCHATBOT_REGISTRATION_EMAIL",
        "academy@example.com",
    )

    with pytest.raises(
        RuntimeError,
        match="EASYCHATBOT_PORTAL_URL",
    ):
        create_academy_one_week_workflow(
            session_factory=MagicMock(),
            email_provider_manager=MagicMock(
                spec=EmailProviderManager,
            ),
        )


def test_missing_production_registration_email_blocks_composition(
    monkeypatch,
):
    """
    Production composition must fail closed when the registration
    email is absent.
    """

    monkeypatch.setenv(
        "EASYCHATBOT_PORTAL_URL",
        "https://academy.example.com",
    )

    monkeypatch.delenv(
        "EASYCHATBOT_REGISTRATION_EMAIL",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="EASYCHATBOT_REGISTRATION_EMAIL",
    ):
        create_academy_one_week_workflow(
            session_factory=MagicMock(),
            email_provider_manager=MagicMock(
                spec=EmailProviderManager,
            ),
        )


def test_production_readiness_does_not_activate_external_delivery(
    monkeypatch,
):
    """
    Configuration readiness must not send email or Telegram.
    """

    monkeypatch.setenv(
        "EASYCHATBOT_PORTAL_URL",
        "https://academy.example.com",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_REGISTRATION_EMAIL",
        "academy@example.com",
    )

    provider_manager = MagicMock(
        spec=EmailProviderManager,
    )

    telegram_bot = MagicMock(
        name="existing_telegram_bot",
    )

    workflow = create_academy_one_week_workflow(
        session_factory=MagicMock(),
        email_provider_manager=provider_manager,
        telegram_bot=telegram_bot,
    )

    assert workflow is not None

    assert provider_manager.method_calls == []
    assert telegram_bot.method_calls == []


def test_production_readiness_does_not_create_scheduler(
    monkeypatch,
):
    """
    Academy production configuration must not create or own a
    scheduler.
    """

    monkeypatch.setenv(
        "EASYCHATBOT_PORTAL_URL",
        "https://academy.example.com",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_REGISTRATION_EMAIL",
        "academy@example.com",
    )

    workflow = create_academy_one_week_workflow(
        session_factory=MagicMock(),
        email_provider_manager=MagicMock(
            spec=EmailProviderManager,
        ),
    )

    assert not hasattr(
        workflow,
        "scheduler",
    )
