from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.announcement.announcement_composer import (
    AnnouncementComposer,
)
from app.application.announcement.announcement_publisher import (
    ControlledAnnouncementPublisher,
)
from app.api.announcement_controls import (
    create_announcement_router,
)


@dataclass
class FakeTelegramMessage:
    message_id: int


class FakeTelegramClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def send_message(
        self,
        *,
        chat_id: str,
        text: str,
        parse_mode: str,
    ) -> FakeTelegramMessage:
        self.calls.append(
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            }
        )

        return FakeTelegramMessage(
            message_id=123,
        )


def create_test_app(
    *,
    client: FakeTelegramClient,
    authorized: bool = True,
    publishing_enabled: bool = True,
) -> FastAPI:
    publisher = ControlledAnnouncementPublisher(
        publisher=_TelegramPublisherDouble(
            client=client,
        ),
        publishing_enabled=publishing_enabled,
    )

    async def authorize_admin() -> bool:
        return authorized

    router = create_announcement_router(
        publisher=publisher,
        composer=AnnouncementComposer(),
        admin_authorizer=authorize_admin,
    )

    app = FastAPI()
    app.include_router(router)

    return app


class _TelegramPublisherDouble:
    """Small test double implementing AnnouncementPublisher."""

    def __init__(
        self,
        *,
        client: FakeTelegramClient,
    ) -> None:
        self._client = client

    async def publish(
        self,
        *,
        channel_id: str,
        text: str,
    ) -> str:
        result = await self._client.send_message(
            chat_id=channel_id,
            text=text,
            parse_mode="Markdown",
        )

        return str(result.message_id)


@pytest.fixture
def telegram_client() -> FakeTelegramClient:
    return FakeTelegramClient()


def test_admin_can_publish_announcement(
    telegram_client: FakeTelegramClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "BETA1_ANNOUNCEMENT_CHANNEL_ID",
        "-100123456789",
    )

    app = create_test_app(
        client=telegram_client,
        authorized=True,
    )

    with TestClient(app) as client:
        response = client.post(
            "/admin/announcements/publish",
            json={
                "announcement_type": "maintenance",
                "title": "Planned maintenance",
                "body": "The Academy will be temporarily unavailable.",
                "footer": "We will communicate when service is restored.",
            },
        )

    assert response.status_code == 201

    payload = response.json()

    assert payload["channel_id"] == "-100123456789"
    assert payload["message_id"] == "123"
    assert payload["announcement_type"] == "maintenance"

    assert len(telegram_client.calls) == 1

    published_text = telegram_client.calls[0]["text"]

    assert "🛠️ MAINTENANCE" in published_text
    assert "Planned maintenance" in published_text
    assert "Academy will be temporarily unavailable" in published_text
    assert "EasyWorld" in published_text


def test_non_admin_cannot_publish(
    telegram_client: FakeTelegramClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "BETA1_ANNOUNCEMENT_CHANNEL_ID",
        "-100123456789",
    )

    app = create_test_app(
        client=telegram_client,
        authorized=False,
    )

    with TestClient(app) as client:
        response = client.post(
            "/admin/announcements/publish",
            json={
                "announcement_type": "important",
                "title": "Important update",
                "body": "This must not be published.",
            },
        )

    assert response.status_code == 403
    assert telegram_client.calls == []


def test_publishing_disabled_does_not_call_telegram(
    telegram_client: FakeTelegramClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "BETA1_ANNOUNCEMENT_CHANNEL_ID",
        "-100123456789",
    )

    app = create_test_app(
        client=telegram_client,
        authorized=True,
        publishing_enabled=False,
    )

    with TestClient(app) as client:
        response = client.post(
            "/admin/announcements/publish",
            json={
                "announcement_type": "beta_update",
                "title": "Beta update",
                "body": "Publishing is currently disabled.",
            },
        )

    assert response.status_code == 503
    assert telegram_client.calls == []


def test_invalid_announcement_is_rejected_before_telegram(
    telegram_client: FakeTelegramClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "BETA1_ANNOUNCEMENT_CHANNEL_ID",
        "-100123456789",
    )

    app = create_test_app(
        client=telegram_client,
        authorized=True,
    )

    with TestClient(app) as client:
        response = client.post(
            "/admin/announcements/publish",
            json={
                "announcement_type": "important",
                "title": "",
                "body": "Invalid announcement.",
            },
        )

    assert response.status_code == 422
    assert telegram_client.calls == []


def test_announcement_type_is_validated(
    telegram_client: FakeTelegramClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "BETA1_ANNOUNCEMENT_CHANNEL_ID",
        "-100123456789",
    )

    app = create_test_app(
        client=telegram_client,
        authorized=True,
    )

    with TestClient(app) as client:
        response = client.post(
            "/admin/announcements/publish",
            json={
                "announcement_type": "not_a_real_type",
                "title": "Invalid type",
                "body": "This should not publish.",
            },
        )

    assert response.status_code == 422
    assert telegram_client.calls == []