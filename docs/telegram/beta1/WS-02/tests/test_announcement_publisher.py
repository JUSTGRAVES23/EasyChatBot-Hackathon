from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.announcement_publisher import (
    ControlledAnnouncementPublisher,
    PublicationDisabledError,
)
from src.telegram_announcement_publisher import (
    TelegramAnnouncementPublisher,
)


@dataclass
class FakeTelegramMessage:
    message_id: int


class FakeTelegramClient:
    def __init__(self) -> None:
        self.calls = []

    async def send_message(
        self,
        *,
        chat_id: str,
        text: str,
        parse_mode: str,
    ):
        self.calls.append(
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            }
        )
        return FakeTelegramMessage(message_id=42)


@pytest.mark.asyncio
async def test_telegram_publisher_is_thin_adapter():
    client = FakeTelegramClient()

    publisher = TelegramAnnouncementPublisher(
        telegram_client=client
    )

    message_id = await publisher.publish(
        channel_id="-100123",
        text="Hello",
    )

    assert message_id == "42"
    assert client.calls == [
        {
            "chat_id": "-100123",
            "text": "Hello",
            "parse_mode": "Markdown",
        }
    ]


@pytest.mark.asyncio
async def test_controlled_publisher_blocks_when_disabled():
    client = FakeTelegramClient()

    publisher = ControlledAnnouncementPublisher(
        publisher=TelegramAnnouncementPublisher(
            telegram_client=client
        ),
        publishing_enabled=False,
    )

    with pytest.raises(PublicationDisabledError):
        await publisher.publish(
            channel_id="-100123",
            text="Hello",
            announcement_type="important",
        )

    assert client.calls == []


@pytest.mark.asyncio
async def test_controlled_publisher_records_success():
    client = FakeTelegramClient()

    publisher = ControlledAnnouncementPublisher(
        publisher=TelegramAnnouncementPublisher(
            telegram_client=client
        ),
        publishing_enabled=True,
    )

    record = await publisher.publish(
        channel_id="-100123",
        text="Hello",
        announcement_type="important",
    )

    assert record.channel_id == "-100123"
    assert record.message_id == "42"
    assert record.announcement_type == "important"
    assert record.published_at is not None
