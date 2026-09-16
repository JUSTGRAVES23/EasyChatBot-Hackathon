from __future__ import annotations

import inspect
from unittest.mock import MagicMock

import pytest

from app.application.academy.academy_one_week_workflow import (
    AcademyOneWeekWorkflow,
)
from app.application.academy_notification_service import (
    OneWeekNotificationOrchestrator,
)
from app.application.composition.academy_production import (
    DisabledAcademyTelegramSender,
    create_academy_one_week_workflow,
)
from app.infrastructure.academy.postgresql_academy_notification_repository import (
    PostgreSQLAcademyDeliveryRepository,
    PostgreSQLAcademyUserQuery,
)
from app.infrastructure.email.academy_email_notification_sender import (
    AcademyEmailNotificationSender,
)
from app.infrastructure.telegram.academy_notification_telegram import (
    ExistingBotTelegramNotificationSender,
)
from cybersecurity.email.email_provider_manager import (
    EmailProviderManager,
)


pytestmark = pytest.mark.integration


def test_academy_composition_builds_with_injected_dependencies():
    """Verify the complete Academy composition is created."""

    session_factory = MagicMock(
        name="session_factory",
    )

    provider_manager = MagicMock(
        spec=EmailProviderManager,
        name="provider_manager",
    )

    workflow = create_academy_one_week_workflow(
        session_factory=session_factory,
        email_provider_manager=provider_manager,
        portal_url="https://example.com",
        registration_email="academy@example.com",
    )

    assert isinstance(
        workflow,
        AcademyOneWeekWorkflow,
    )

    # Existing PostgreSQL repository implementations.
    assert isinstance(
        workflow._users,
        PostgreSQLAcademyUserQuery,
    )

    assert isinstance(
        workflow._deliveries,
        PostgreSQLAcademyDeliveryRepository,
    )

    assert (
        workflow._users._session_factory
        is session_factory
    )

    assert (
        workflow._deliveries._session_factory
        is session_factory
    )

    # Existing Academy application orchestrator.
    assert isinstance(
        workflow._notifications,
        OneWeekNotificationOrchestrator,
    )

    # Existing email provider boundary.
    assert isinstance(
        workflow._notifications._email_sender,
        AcademyEmailNotificationSender,
    )

    assert (
        workflow
        ._notifications
        ._email_sender
        ._provider_manager
        is provider_manager
    )


def test_academy_composition_does_not_require_telegram_bot():
    """
    Academy composition must remain constructible without
    creating a second Telegram client.
    """

    session_factory = MagicMock(
        name="session_factory",
    )

    provider_manager = MagicMock(
        spec=EmailProviderManager,
        name="provider_manager",
    )

    workflow = create_academy_one_week_workflow(
        session_factory=session_factory,
        email_provider_manager=provider_manager,
        portal_url="https://example.com",
        registration_email="academy@example.com",
    )

    telegram_sender = (
        workflow
        ._notifications
        ._telegram_sender
    )

    assert isinstance(
        telegram_sender,
        DisabledAcademyTelegramSender,
    )


def test_academy_composition_accepts_existing_telegram_bot():
    """
    The existing Telegram Bot instance must be reused.

    Academy must not create another Telegram client.
    """

    session_factory = MagicMock(
        name="session_factory",
    )

    provider_manager = MagicMock(
        spec=EmailProviderManager,
        name="provider_manager",
    )

    existing_bot = MagicMock(
        name="existing_telegram_bot",
    )

    workflow = create_academy_one_week_workflow(
        session_factory=session_factory,
        email_provider_manager=provider_manager,
        telegram_bot=existing_bot,
        portal_url="https://example.com",
        registration_email="academy@example.com",
    )

    sender = (
        workflow
        ._notifications
        ._telegram_sender
    )

    assert isinstance(
        sender,
        ExistingBotTelegramNotificationSender,
    )

    assert sender._bot is existing_bot

    # Construction must not call the existing Bot.
    assert existing_bot.method_calls == []


def test_academy_composition_does_not_create_scheduler():
    """
    Scheduler ownership remains outside Academy composition.
    """

    session_factory = MagicMock(
        name="session_factory",
    )

    provider_manager = MagicMock(
        spec=EmailProviderManager,
        name="provider_manager",
    )

    workflow = create_academy_one_week_workflow(
        session_factory=session_factory,
        email_provider_manager=provider_manager,
        portal_url="https://example.com",
        registration_email="academy@example.com",
    )

    assert isinstance(
        workflow,
        AcademyOneWeekWorkflow,
    )

    assert not hasattr(
        workflow,
        "scheduler",
    )


def test_academy_composition_performs_no_external_delivery():
    """
    Constructing the composition must not send email or Telegram.
    """

    session_factory = MagicMock(
        name="session_factory",
    )

    provider_manager = MagicMock(
        spec=EmailProviderManager,
        name="provider_manager",
    )

    existing_bot = MagicMock(
        name="existing_telegram_bot",
    )

    workflow = create_academy_one_week_workflow(
        session_factory=session_factory,
        email_provider_manager=provider_manager,
        telegram_bot=existing_bot,
        portal_url="https://example.com",
        registration_email="academy@example.com",
    )

    email_sender = (
        workflow
        ._notifications
        ._email_sender
    )

    telegram_sender = (
        workflow
        ._notifications
        ._telegram_sender
    )

    assert inspect.iscoroutinefunction(
        email_sender.send,
    )

    assert inspect.iscoroutinefunction(
        telegram_sender.send,
    )

    # No external provider operation occurred.
    assert provider_manager.method_calls == []
    assert existing_bot.method_calls == []


def test_missing_portal_configuration_is_rejected(
    monkeypatch,
):
    """
    Portal URL must be explicitly configured when not injected.
    """

    monkeypatch.delenv(
        "EASYCHATBOT_PORTAL_URL",
        raising=False,
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
            registration_email="academy@example.com",
        )


def test_missing_registration_email_configuration_is_rejected(
    monkeypatch,
):
    """
    Registration email must be explicitly configured when not injected.
    """

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
            portal_url="https://example.com",
        )
