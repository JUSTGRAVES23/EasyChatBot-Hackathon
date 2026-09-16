from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.developer_admin.developer_admin_audit import (
    DeveloperAdminAuditService,
    DeveloperAdminAuditValidationError,
)


class FakeAuditRepository:
    def __init__(self) -> None:
        self.events = []

    async def record(self, event):
        self.events.append(event)
        return event


@pytest.mark.asyncio
async def test_record_change_creates_safe_event():
    repository = FakeAuditRepository()
    service = DeveloperAdminAuditService(repository)

    actor = uuid4()
    target = uuid4()

    event = await service.record_change(
        event_type=DeveloperAdminAuditService.GRANTED,
        actor_user_id=actor,
        target_user_id=target,
        actor_email="actor@example.com",
        target_email="target@example.com",
        correlation_id="corr-123",
        metadata={"operation": "grant"},
    )

    assert event.event_type == "developer_admin.granted"
    assert event.actor_user_id == actor
    assert event.target_user_id == target
    assert event.outcome == "success"
    assert dict(event.metadata) == {"operation": "grant"}
    assert repository.events == [event]


@pytest.mark.asyncio
async def test_rejects_unsafe_metadata():
    service = DeveloperAdminAuditService(FakeAuditRepository())

    with pytest.raises(DeveloperAdminAuditValidationError):
        await service.record_change(
            event_type=DeveloperAdminAuditService.GRANTED,
            actor_user_id=uuid4(),
            target_user_id=uuid4(),
            actor_email="actor@example.com",
            target_email="target@example.com",
            metadata={"password": "must-not-be-recorded"},
        )


@pytest.mark.asyncio
async def test_rejects_unknown_event_type():
    service = DeveloperAdminAuditService(FakeAuditRepository())

    with pytest.raises(DeveloperAdminAuditValidationError):
        await service.record_change(
            event_type="developer_admin.deleted",
            actor_user_id=uuid4(),
            target_user_id=uuid4(),
            actor_email="actor@example.com",
            target_email="target@example.com",
        )
