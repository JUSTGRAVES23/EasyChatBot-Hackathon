from __future__ import annotations

import os

from app.application.academy_notification_formatters import (
    AcademyEmailFormatter,
    AcademyTelegramFormatter,
)

from app.application.academy_notification_ports import (
    TelegramNotificationSender,
)

from app.application.academy_notification_service import (
    OneWeekNotificationOrchestrator,
)
from app.application.academy.academy_one_week_workflow import (
    AcademyOneWeekWorkflow,
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
from app.infrastructure.persistence.database import (
    create_async_database_engine,
    create_async_session_factory,
)
from cybersecurity.email.email_provider_manager import (
    EmailProviderManager,
)


class DisabledAcademyTelegramSender:
    """Safe default when no existing Telegram Bot is supplied.

    Academy email delivery remains independently testable.
    No second Telegram Bot is created.
    """

    async def send(
        self,
        *,
        chat_id: str,
        text: str,
        portal_url: str,
    ) -> dict:
        return {
            "provider": "telegram",
            "status": "not_configured",
            "message_id": None,
        }


def _required_config(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"{name} is required for Academy production composition."
        )

    return value


def create_academy_one_week_workflow(
    *,
    session_factory=None,
    email_provider_manager: EmailProviderManager | None = None,
    telegram_bot=None,
    portal_url: str | None = None,
    registration_email: str | None = None,
) -> AcademyOneWeekWorkflow:
    """Compose the production Academy one-week workflow.

    Composition:

        PostgreSQL
            ↓
        AcademyOneWeekWorkflow
            ↓
        OneWeekNotificationOrchestrator
            ↓
        EmailProviderManager
            ↓
        Existing Telegram Bot adapter

    The scheduler itself is intentionally not created here.
    """

    if session_factory is None:
        engine = create_async_database_engine()
        session_factory = create_async_session_factory(engine)

    resolved_portal_url = (
        portal_url.strip()
        if portal_url is not None
        else _required_config("EASYCHATBOT_PORTAL_URL")
    )

    resolved_registration_email = (
        registration_email.strip()
        if registration_email is not None
        else _required_config("EASYCHATBOT_REGISTRATION_EMAIL")
    )

    email_sender = AcademyEmailNotificationSender(
        provider_manager=email_provider_manager
        or EmailProviderManager()
    )

    if telegram_bot is not None:
        telegram_sender: TelegramNotificationSender = (
            ExistingBotTelegramNotificationSender(
                telegram_bot,
            )
        )
    else:
        telegram_sender = DisabledAcademyTelegramSender()

    notifications = OneWeekNotificationOrchestrator(
        email_sender=email_sender,
        telegram_sender=telegram_sender,
        email_formatter=AcademyEmailFormatter(),
        telegram_formatter=AcademyTelegramFormatter(),
        registration_email=resolved_registration_email,
        portal_url=resolved_portal_url,
    )

    users = PostgreSQLAcademyUserQuery(
        session_factory,
    )

    deliveries = PostgreSQLAcademyDeliveryRepository(
        session_factory,
    )

    return AcademyOneWeekWorkflow(
        users=users,
        deliveries=deliveries,
        notifications=notifications,
    )


__all__ = [
    "create_academy_one_week_workflow",
]

