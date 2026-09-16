from __future__ import annotations

from datetime import datetime, timedelta

from .academy_notification_formatters import AcademyEmailFormatter, AcademyTelegramFormatter
from .academy_notification_ports import EmailNotificationSender, TelegramNotificationSender
from ..domain.academy_notification import (
    AcademyNotification,
    AcademyNotificationType,
)


class OneWeekNotificationOrchestrator:
    """Coordinates the 1-week milestone across Email and Telegram."""

    def __init__(
        self,
        *,
        email_sender: EmailNotificationSender,
        telegram_sender: TelegramNotificationSender,
        email_formatter: AcademyEmailFormatter,
        telegram_formatter: AcademyTelegramFormatter,
        registration_email: str,
        portal_url: str,
    ) -> None:
        if not registration_email.strip():
            raise ValueError("registration_email cannot be empty.")
        if not portal_url.strip():
            raise ValueError("portal_url cannot be empty.")

        self._email_sender = email_sender
        self._telegram_sender = telegram_sender
        self._email_formatter = email_formatter
        self._telegram_formatter = telegram_formatter
        self._registration_email = registration_email
        self._portal_url = portal_url

    @staticmethod
    def is_one_week_eligible(
        *,
        registered_at: datetime,
        now: datetime,
    ) -> bool:
        if registered_at.tzinfo is None or now.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware.")
        age = now - registered_at
        return timedelta(days=7) <= age < timedelta(days=8)

    async def send_one_week(
        self,
        *,
        email: str,
        username: str,
        telegram_chat_id: str | None,
    ) -> dict:
        notification = AcademyNotification(
            notification_type=AcademyNotificationType.ONE_WEEK_MILESTONE,
            username=username,
            portal_url=self._portal_url,
        )

        rendered_email = self._email_formatter.render(notification)

        email_result = await self._email_sender.send(
            "🎓 One Week at EasyChatBot, "
            f"@{username.strip()}!",
            {
                "recipient": email,
                "email_type": "academy_notification",
                "notification_type": notification.notification_type.value,
                "from": self._registration_email,
                "body": rendered_email["body"],
                "html": rendered_email["html"],
                "attachments": rendered_email.get(
                    "attachments",
                    [],
                ),
            },
        )

        telegram_result = None
        if telegram_chat_id:
            telegram_result = await self._telegram_sender.send(
                chat_id=telegram_chat_id,
                text=self._telegram_formatter.render(notification),
                portal_url=self._portal_url,
            )

        return {
            "notification_type": notification.notification_type.value,
            "email": email_result,
            "telegram": telegram_result,
        }
