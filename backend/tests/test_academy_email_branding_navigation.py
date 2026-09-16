from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.application.academy_notification_formatters import (
    AcademyEmailFormatter,
    AcademyTelegramFormatter,
)
from app.application.academy_notification_service import (
    OneWeekNotificationOrchestrator,
)
from app.domain.academy_notification import (
    AcademyNotification,
    AcademyNotificationType,
)


class FakeEmail:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def send(self, subject: str, content: dict) -> dict:
        self.calls.append((subject, content))
        return {"provider": "fake-email", "status": "accepted"}


class FakeTelegram:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def send(self, *, chat_id: str, text: str, portal_url: str) -> dict:
        self.calls.append(
            {
                "chat_id": chat_id,
                "text": text,
                "portal_url": portal_url,
            }
        )
        return {"provider": "fake-telegram", "status": "accepted"}


def _notification() -> AcademyNotification:
    return AcademyNotification(
        AcademyNotificationType.ONE_WEEK_MILESTONE,
        "Davideasychabot",
        "http://localhost:3000/dashboard",
    )


def test_email_has_clickable_main_and_footer_logo(tmp_path: Path) -> None:
    logo = tmp_path / "easychatbot-logo.png"
    logo.write_bytes(b"test")

    rendered = AcademyEmailFormatter(logo_path=logo).render(_notification())
    html = rendered["html"]

    assert html.count('href="http://localhost:3000/dashboard"') >= 3
    assert html.count("cid:easychatbot-logo") == 2
    assert rendered["attachments"] == [
        {
            "path": str(logo),
            "filename": "easychatbot-logo.png",
            "inline": True,
            "content_id": "easychatbot-logo",
        }
    ]


def test_email_has_configuration_driven_social_destinations(tmp_path: Path) -> None:
    logo = tmp_path / "easychatbot-logo.png"
    logo.write_bytes(b"test")

    rendered = AcademyEmailFormatter(
        logo_path=logo,
        x_url="https://example.com/x",
        instagram_url="https://example.com/instagram",
        linkedin_url="https://example.com/linkedin",
        youtube_url="https://example.com/youtube",
    ).render(_notification())

    html = rendered["html"]

    assert 'href="https://example.com/x"' in html
    assert 'href="https://example.com/instagram"' in html
    assert 'href="https://example.com/linkedin"' in html
    assert 'href="https://example.com/youtube"' in html


def test_telegram_keeps_portal_button_contract() -> None:
    text = AcademyTelegramFormatter().render(_notification())
    assert "@Davideasychabot" in text
    assert "Congratulations" in text


def test_orchestrator_passes_inline_logo_asset() -> None:
    import asyncio

    async def run() -> None:
        email = FakeEmail()
        telegram = FakeTelegram()

        # The production formatter validates the logo path. A deterministic
        # temporary logo is used for this integration-level unit test.
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            logo = Path(directory) / "easychatbot-logo.png"
            logo.write_bytes(b"test")

            service = OneWeekNotificationOrchestrator(
                email_sender=email,
                telegram_sender=telegram,
                email_formatter=AcademyEmailFormatter(logo_path=logo),
                telegram_formatter=AcademyTelegramFormatter(),
                registration_email="registrationeasychatbot@resend.dev",
                portal_url="http://localhost:3000/dashboard",
            )

            result = await service.send_one_week(
                email="test@example.com",
                username="Davideasychabot",
                telegram_chat_id="123456",
            )

            content = email.calls[0][1]
            assert content["from"] == "registrationeasychatbot@resend.dev"
            assert content["email_type"] == "academy_notification"
            assert content["attachments"][0]["inline"] is True
            assert content["attachments"][0]["content_id"] == "easychatbot-logo"
            assert result["notification_type"] == "1_WEEK_MILESTONE"
            assert telegram.calls[0]["chat_id"] == "123456"
            assert telegram.calls[0]["portal_url"] == "http://localhost:3000/dashboard"

    asyncio.run(run())


def test_one_week_eligibility_window() -> None:
    now = datetime.now(timezone.utc)
    assert OneWeekNotificationOrchestrator.is_one_week_eligible(
        registered_at=now - timedelta(days=7),
        now=now,
    )
    assert not OneWeekNotificationOrchestrator.is_one_week_eligible(
        registered_at=now - timedelta(days=6),
        now=now,
    )

