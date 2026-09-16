import asyncio
from datetime import datetime, timedelta, timezone

from easychatbot_1_week_milestone.application.academy_notification_service import (
    OneWeekNotificationOrchestrator,
)
from easychatbot_1_week_milestone.application.formatters import (
    AcademyEmailFormatter,
    AcademyTelegramFormatter,
)


class FakeEmail:
    def __init__(self):
        self.calls = []

    async def send(self, subject, content):
        self.calls.append((subject, content))
        return {"provider": "fake-email", "status": "accepted"}


class FakeTelegram:
    def __init__(self):
        self.calls = []

    async def send(self, *, chat_id, text, portal_url):
        self.calls.append(
            {"chat_id": chat_id, "text": text, "portal_url": portal_url}
        )
        return {"provider": "fake-telegram", "status": "accepted"}


def test_one_week_eligibility():
    now = datetime.now(timezone.utc)
    assert OneWeekNotificationOrchestrator.is_one_week_eligible(
        registered_at=now - timedelta(days=7), now=now
    )
    assert not OneWeekNotificationOrchestrator.is_one_week_eligible(
        registered_at=now - timedelta(days=6), now=now
    )


def test_email_formatter():
    from easychatbot_1_week_milestone.domain.academy_notification import (
        AcademyNotification,
        AcademyNotificationType,
    )

    n = AcademyNotification(
        AcademyNotificationType.ONE_WEEK_MILESTONE,
        "Davideasychabot",
        "http://localhost:3000/dashboard",
    )
    rendered = AcademyEmailFormatter().render(n)

    assert "@Davideasychabot" in rendered["html"]
    assert "http://localhost:3000/dashboard" in rendered["html"]
    assert "Continue Learning" in rendered["html"]
    assert "cid:easychatbot-logo" in rendered["html"]
    assert "Critical findings:" not in rendered["html"]


def test_telegram_formatter():
    from easychatbot_1_week_milestone.domain.academy_notification import (
        AcademyNotification,
        AcademyNotificationType,
    )

    n = AcademyNotification(
        AcademyNotificationType.ONE_WEEK_MILESTONE,
        "Davideasychabot",
        "http://localhost:3000/dashboard",
    )
    text = AcademyTelegramFormatter().render(n)

    assert "@Davideasychabot" in text
    assert "Congratulations" in text


def test_orchestrator():
    async def run():
        email = FakeEmail()
        telegram = FakeTelegram()
        service = OneWeekNotificationOrchestrator(
            email_sender=email,
            telegram_sender=telegram,
            email_formatter=AcademyEmailFormatter(),
            telegram_formatter=AcademyTelegramFormatter(),
            registration_email="registrationeasychatbot@resend.dev",
            portal_url="http://localhost:3000/dashboard",
        )

        result = await service.send_one_week(
            email="davdbarbero1999@gmail.com",
            username="Davideasychabot",
            telegram_chat_id="123456",
        )

        assert result["notification_type"] == "1_WEEK_MILESTONE"
        assert email.calls[0][1]["from"] == "registrationeasychatbot@resend.dev"
        assert telegram.calls[0]["chat_id"] == "123456"
        assert telegram.calls[0]["portal_url"] == "http://localhost:3000/dashboard"

    asyncio.run(run())
