from uuid import uuid4

import pytest

from app.infrastructure.announcements.execution.telegram_publication_publisher_adapter import (
    TelegramPublicationPublisherAdapter,
)


class FakeControlledPublisher:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def publish(
        self,
        *,
        channel_id: str,
        text: str,
        announcement_type: str,
    ):
        self.calls.append(
            {
                "channel_id": channel_id,
                "text": text,
                "announcement_type": announcement_type,
            }
        )

        class Record:
            message_id = "telegram-message-123"

        return Record()


@pytest.mark.asyncio
async def test_ws23_1_4_adapter_delegates_to_controlled_publisher() -> None:
    controlled = FakeControlledPublisher()

    adapter = TelegramPublicationPublisherAdapter(
        publisher=controlled,
        channel_id="-1001234567890",
        announcement_type="beta_update",
    )

    message_id = await adapter.publish(
        publication_id=uuid4(),
        title="Beta 1",
        content="The beta is ready.",
        correlation_id="corr-1",
        idempotency_key="idem-1",
    )

    assert message_id == "telegram-message-123"

    assert controlled.calls == [
        {
            "channel_id": "-1001234567890",
            "text": "*Beta 1*\n\nThe beta is ready.",
            "announcement_type": "beta_update",
        }
    ]


@pytest.mark.asyncio
async def test_ws23_1_4_adapter_rejects_empty_title() -> None:
    controlled = FakeControlledPublisher()

    adapter = TelegramPublicationPublisherAdapter(
        publisher=controlled,
        channel_id="-1001234567890",
    )

    with pytest.raises(ValueError, match="title cannot be empty"):
        await adapter.publish(
            publication_id=uuid4(),
            title=" ",
            content="content",
            correlation_id="corr",
            idempotency_key="idem",
        )


@pytest.mark.asyncio
async def test_ws23_1_4_adapter_rejects_empty_content() -> None:
    controlled = FakeControlledPublisher()

    adapter = TelegramPublicationPublisherAdapter(
        publisher=controlled,
        channel_id="-1001234567890",
    )

    with pytest.raises(ValueError, match="content cannot be empty"):
        await adapter.publish(
            publication_id=uuid4(),
            title="Beta 1",
            content=" ",
            correlation_id="corr",
            idempotency_key="idem",
        )


@pytest.mark.asyncio
async def test_ws23_1_4_adapter_rejects_empty_correlation_id() -> None:
    controlled = FakeControlledPublisher()

    adapter = TelegramPublicationPublisherAdapter(
        publisher=controlled,
        channel_id="-1001234567890",
    )

    with pytest.raises(ValueError, match="correlation_id cannot be empty"):
        await adapter.publish(
            publication_id=uuid4(),
            title="Beta 1",
            content="content",
            correlation_id=" ",
            idempotency_key="idem",
        )


@pytest.mark.asyncio
async def test_ws23_1_4_adapter_rejects_empty_idempotency_key() -> None:
    controlled = FakeControlledPublisher()

    adapter = TelegramPublicationPublisherAdapter(
        publisher=controlled,
        channel_id="-1001234567890",
    )

    with pytest.raises(ValueError, match="idempotency_key cannot be empty"):
        await adapter.publish(
            publication_id=uuid4(),
            title="Beta 1",
            content="content",
            correlation_id="corr",
            idempotency_key=" ",
        )


def test_ws23_1_4_adapter_requires_channel_id() -> None:
    controlled = FakeControlledPublisher()

    with pytest.raises(
        ValueError,
        match="BETA1_ANNOUNCEMENT_CHANNEL_ID is not configured",
    ):
        TelegramPublicationPublisherAdapter(
            publisher=controlled,
            channel_id=" ",
        )
