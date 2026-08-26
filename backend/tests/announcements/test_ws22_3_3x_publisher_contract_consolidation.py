from __future__ import annotations

from uuid import uuid4

import pytest

from backend.app.application.announcements.execution.legacy_publisher_bridge import (
    LegacyAnnouncementPublisherBridge,
)


class RecordingLegacyPublisher:
    """Test double for the existing Beta publisher contract."""

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    async def publish(
        self,
        *,
        channel_id: str,
        text: str,
    ) -> str:
        self.calls.append(
            {
                "channel_id": channel_id,
                "text": text,
            }
        )

        return "legacy-message-001"


@pytest.mark.asyncio
async def test_bridge_implements_canonical_ws22_publisher_contract() -> None:
    publisher = RecordingLegacyPublisher()

    bridge = LegacyAnnouncementPublisherBridge(
        publisher=publisher,
        channel_id="announcement-channel",
    )

    result = await bridge.publish(
        publication_id=uuid4(),
        title="Beta 2",
        content="EasyChatBot Beta 2 is available.",
        correlation_id="corr-001",
        idempotency_key="idem-001",
    )

    assert result == "legacy-message-001"

    assert publisher.calls == [
        {
            "channel_id": "announcement-channel",
            "text": (
                "Beta 2\n\n"
                "EasyChatBot Beta 2 is available."
            ),
        }
    ]


@pytest.mark.asyncio
async def test_bridge_does_not_duplicate_execution_metadata() -> None:
    publisher = RecordingLegacyPublisher()

    bridge = LegacyAnnouncementPublisherBridge(
        publisher=publisher,
        channel_id="announcement-channel",
    )

    await bridge.publish(
        publication_id=uuid4(),
        title="Maintenance",
        content="Scheduled maintenance.",
        correlation_id="corr-sensitive",
        idempotency_key="idem-sensitive",
    )

    assert publisher.calls[0]["text"] == (
        "Maintenance\n\n"
        "Scheduled maintenance."
    )

    assert "corr-sensitive" not in publisher.calls[0]["text"]
    assert "idem-sensitive" not in publisher.calls[0]["text"]


@pytest.mark.asyncio
async def test_bridge_uses_configured_channel() -> None:
    publisher = RecordingLegacyPublisher()

    bridge = LegacyAnnouncementPublisherBridge(
        publisher=publisher,
        channel_id="configured-channel",
    )

    await bridge.publish(
        publication_id=uuid4(),
        title="Release",
        content="New release.",
        correlation_id="corr-001",
        idempotency_key="idem-001",
    )

    assert publisher.calls[0]["channel_id"] == (
        "configured-channel"
    )


def test_bridge_rejects_missing_publisher() -> None:
    with pytest.raises(ValueError, match="publisher cannot be None"):
        LegacyAnnouncementPublisherBridge(
            publisher=None,  # type: ignore[arg-type]
            channel_id="channel",
        )


def test_bridge_rejects_empty_channel() -> None:
    publisher = RecordingLegacyPublisher()

    with pytest.raises(
        ValueError,
        match="channel_id cannot be empty",
    ):
        LegacyAnnouncementPublisherBridge(
            publisher=publisher,
            channel_id=" ",
        )


@pytest.mark.asyncio
async def test_bridge_rejects_empty_title() -> None:
    publisher = RecordingLegacyPublisher()

    bridge = LegacyAnnouncementPublisherBridge(
        publisher=publisher,
        channel_id="channel",
    )

    with pytest.raises(
        ValueError,
        match="title cannot be empty",
    ):
        await bridge.publish(
            publication_id=uuid4(),
            title=" ",
            content="Content",
            correlation_id="corr-001",
            idempotency_key="idem-001",
        )


@pytest.mark.asyncio
async def test_bridge_rejects_empty_content() -> None:
    publisher = RecordingLegacyPublisher()

    bridge = LegacyAnnouncementPublisherBridge(
        publisher=publisher,
        channel_id="channel",
    )

    with pytest.raises(
        ValueError,
        match="content cannot be empty",
    ):
        await bridge.publish(
            publication_id=uuid4(),
            title="Title",
            content=" ",
            correlation_id="corr-001",
            idempotency_key="idem-001",
        )