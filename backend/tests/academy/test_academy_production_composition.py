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
from cybersecurity.scheduler.cybersecurity_scheduler_factory import (
    create_cybersecurity_scheduler_runtime,
)


pytestmark = pytest.mark.integration


def _create_dependencies():
    session_factory = MagicMock(
        name="session_factory",
    )

    provider_manager = MagicMock(
        spec=EmailProviderManager,
        name="provider_manager",
    )

    return (
        session_factory,
        provider_manager,
    )


def test_academy_composition_builds_with_injected_dependencies():
    """
    Academy production composition must construct successfully
    with explicitly injected infrastructure dependencies.
    """

    (
        session_factory,
        provider_manager,
    ) = _create_dependencies()

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

    assert isinstance(
        workflow._users,
        PostgreSQLAcademyUserQuery,
    )

    assert isinstance(
        workflow._deliveries,
        PostgreSQLAcademyDeliveryRepository,
    )

    assert workflow._users._session_factory is session_factory
    assert workflow._deliveries._session_factory is session_factory

    assert isinstance(
        workflow._notifications,
        OneWeekNotificationOrchestrator,
    )

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
    Academy must remain constructible without creating another
    Telegram client.
    """

    (
        session_factory,
        provider_manager,
    ) = _create_dependencies()

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


def test_academy_composition_reuses_existing_telegram_bot():
    """
    Academy must reuse the existing outbound Telegram Bot instance.
    """

    (
        session_factory,
        provider_manager,
    ) = _create_dependencies()

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
    Academy composition itself must not own or create a scheduler.
    """

    (
        session_factory,
        provider_manager,
    ) = _create_dependencies()

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

    # The real Academy workflow must not expose scheduler ownership.
    assert "scheduler" not in vars(workflow)


def test_academy_composition_performs_no_external_delivery():
    """
    Composition must not perform email or Telegram delivery.
    """

    (
        session_factory,
        provider_manager,
    ) = _create_dependencies()

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


def test_existing_scheduler_accepts_academy_workflow():
    """
    Academy must be injected into the existing shared scheduler.
    """

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    runtime = create_cybersecurity_scheduler_runtime(
        workflow_service=MagicMock(),
        academy_one_week_workflow=academy_workflow,
    )

    assert (
        runtime
        .scheduler_adapter
        .academy_one_week_workflow
        is academy_workflow
    )


def test_existing_scheduler_is_not_started_during_composition():
    """
    Creating the scheduler runtime must not start APScheduler.
    """

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    runtime = create_cybersecurity_scheduler_runtime(
        workflow_service=MagicMock(),
        academy_one_week_workflow=academy_workflow,
    )

    assert (
        runtime
        .scheduler_adapter
        .scheduler
        .running
        is False
    )


def test_academy_scheduler_composition_creates_only_one_scheduler():
    """
    The existing scheduler owns the scheduler instance.

    Academy receives the workflow but does not own scheduler
    infrastructure.
    """

    academy_workflow = create_academy_one_week_workflow(
        session_factory=MagicMock(
            name="session_factory",
        ),
        email_provider_manager=MagicMock(
            spec=EmailProviderManager,
            name="provider_manager",
        ),
        portal_url="https://example.com",
        registration_email="academy@example.com",
    )

    runtime = create_cybersecurity_scheduler_runtime(
        workflow_service=MagicMock(),
        academy_one_week_workflow=academy_workflow,
    )

    adapter = runtime.scheduler_adapter

    assert adapter.scheduler is not None

    assert adapter.scheduler.running is False

    assert (
        adapter.academy_one_week_workflow
        is academy_workflow
    )

    assert isinstance(
        academy_workflow,
        AcademyOneWeekWorkflow,
    )

    # Academy workflow does not own scheduler infrastructure.
    assert "scheduler" not in vars(academy_workflow)


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
