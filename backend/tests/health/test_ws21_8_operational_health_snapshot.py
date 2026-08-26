from __future__ import annotations

import pytest

from app.application.health.dependency_checks import (
    AsyncDependencyCheck,
    ConfigurationCheck,
)
from app.application.health.health_result import (
    HealthStatus,
)
from app.application.health.operational_health_snapshot import (
    OperationalEvent,
    OperationalEventType,
    OperationalHealthSnapshotService,
    OperationalSurface,
)
from app.application.health.production_readiness_service import (
    ProductionReadinessService,
)


class FakeIdentityResolver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def resolve(
        self,
        user_reference: str,
    ) -> str | None:
        self.calls.append(
            user_reference
        )

        return (
            f"telegram-user:{user_reference}"
        )


async def healthy_probe():
    return True


def make_readiness_service():
    return ProductionReadinessService(
        checks=(
            ConfigurationCheck(
                name="telegram",
                configured=True,
            ),
            AsyncDependencyCheck(
                name="postgresql",
                probe=healthy_probe,
            ),
            AsyncDependencyCheck(
                name="llm_provider",
                probe=healthy_probe,
            ),
        )
    )


@pytest.mark.asyncio
async def test_ws21_8_complete_operational_snapshot():

    service = (
        OperationalHealthSnapshotService(
            readiness_service=(
                make_readiness_service()
            )
        )
    )

    snapshot = await service.create_snapshot()

    assert snapshot.ready is True

    assert (
        snapshot.overall_status
        is HealthStatus.HEALTHY
    )

    assert (
        snapshot.postgresql_status
        is HealthStatus.HEALTHY
    )

    assert (
        snapshot.llm_status
        is HealthStatus.HEALTHY
    )

    assert (
        snapshot.telegram_status
        is HealthStatus.HEALTHY
    )


@pytest.mark.asyncio
async def test_ws21_8_dependency_failure_is_sanitized():

    async def failing_database():
        raise RuntimeError(
            "DATABASE_URL=postgresql://user:password@host/db"
        )

    readiness = ProductionReadinessService(
        checks=(
            AsyncDependencyCheck(
                name="postgresql",
                probe=failing_database,
            ),
            ConfigurationCheck(
                name="telegram",
                configured=True,
            ),
        )
    )

    service = (
        OperationalHealthSnapshotService(
            readiness_service=readiness
        )
    )

    snapshot = await service.create_snapshot()

    assert snapshot.ready is False

    payload = snapshot.as_dict()

    serialized = str(payload).lower()

    assert "password" not in serialized
    assert "postgresql://user" not in serialized
    assert "database_url" not in serialized


@pytest.mark.asyncio
async def test_ws21_8_correlation_user_and_world_are_preserved():

    resolver = FakeIdentityResolver()

    service = (
        OperationalHealthSnapshotService(
            readiness_service=(
                make_readiness_service()
            ),
            identity_resolver=resolver,
        )
    )

    event = OperationalEvent(
        event_type=(
            OperationalEventType.MESSAGE_FAILURE
        ),
        surface=(
            OperationalSurface.PRIVATE_CLASSROOM
        ),
        correlation_id="corr-001",
        user_reference="user-ref-001",
        world_id="world-fr",
    )

    snapshot = await service.create_snapshot(
        events=(event,)
    )

    assert len(snapshot.events) == 1

    stored = snapshot.events[0]

    assert (
        stored.correlation_id
        == "corr-001"
    )

    assert (
        stored.user_reference
        == "telegram-user:user-ref-001"
    )

    assert (
        stored.world_id
        == "world-fr"
    )

    assert resolver.calls == [
        "user-ref-001"
    ]


@pytest.mark.asyncio
async def test_ws21_8_rate_limit_and_abuse_events_are_represented():

    service = (
        OperationalHealthSnapshotService(
            readiness_service=(
                make_readiness_service()
            )
        )
    )

    events = (
        OperationalEvent(
            event_type=(
                OperationalEventType.RATE_LIMIT
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="rate-001",
            user_reference="user-001",
            world_id="world-fr",
        ),
        OperationalEvent(
            event_type=(
                OperationalEventType.ABUSE
            ),
            surface=(
                OperationalSurface.PRIVATE_CLASSROOM
            ),
            correlation_id="abuse-001",
            user_reference="user-002",
            world_id="world-es",
        ),
    )

    snapshot = await service.create_snapshot(
        events=events
    )

    event_types = {
        event.event_type
        for event in snapshot.events
    }

    assert (
        OperationalEventType.RATE_LIMIT
        in event_types
    )

    assert (
        OperationalEventType.ABUSE
        in event_types
    )


@pytest.mark.asyncio
async def test_ws21_8_message_failure_is_represented_without_message_content():

    service = (
        OperationalHealthSnapshotService(
            readiness_service=(
                make_readiness_service()
            )
        )
    )

    event = OperationalEvent(
        event_type=(
            OperationalEventType.MESSAGE_FAILURE
        ),
        surface=(
            OperationalSurface.PRIVATE_CLASSROOM
        ),
        correlation_id="failure-001",
        user_reference="user-001",
        world_id="world-fr",
        metadata={
            "error_type": "TimeoutError",
        },
    )

    snapshot = await service.create_snapshot(
        events=(event,)
    )

    payload = snapshot.as_dict()

    assert (
        len(
            payload[
                "private_classroom_events"
            ]
        )
        == 1
    )

    assert (
        "message"
        not in payload[
            "private_classroom_events"
        ][0]["metadata"]
    )


@pytest.mark.asyncio
async def test_ws21_8_private_and_announcement_surfaces_are_separate():

    service = (
        OperationalHealthSnapshotService(
            readiness_service=(
                make_readiness_service()
            )
        )
    )

    private_event = OperationalEvent(
        event_type=(
            OperationalEventType.MESSAGE_FAILURE
        ),
        surface=(
            OperationalSurface.PRIVATE_CLASSROOM
        ),
        correlation_id="private-001",
    )

    announcement_event = OperationalEvent(
        event_type=(
            OperationalEventType.TELEGRAM_FAILURE
        ),
        surface=(
            OperationalSurface.ANNOUNCEMENT_GROUP
        ),
        correlation_id="announcement-001",
    )

    snapshot = await service.create_snapshot(
        events=(
            private_event,
            announcement_event,
        )
    )

    assert len(
        snapshot.private_classroom_events
    ) == 1

    assert len(
        snapshot.announcement_group_events
    ) == 1

    assert (
        snapshot.private_classroom_events[0]
        .surface
        is OperationalSurface.PRIVATE_CLASSROOM
    )

    assert (
        snapshot.announcement_group_events[0]
        .surface
        is OperationalSurface.ANNOUNCEMENT_GROUP
    )


@pytest.mark.asyncio
async def test_ws21_8_sensitive_metadata_is_removed():

    service = (
        OperationalHealthSnapshotService(
            readiness_service=(
                make_readiness_service()
            )
        )
    )

    event = OperationalEvent(
        event_type=(
            OperationalEventType.PROVIDER_FAILURE
        ),
        surface=(
            OperationalSurface.PRIVATE_CLASSROOM
        ),
        correlation_id="provider-001",
        metadata={
            "provider": "ollama",
            "api_key": "SECRET-123",
            "password": "SECRET-PASSWORD",
            "database_url": (
                "postgresql://user:password@host/db"
            ),
            "safe_status": "timeout",
        },
    )

    snapshot = await service.create_snapshot(
        events=(event,)
    )

    payload = str(
        snapshot.as_dict()
    ).lower()

    assert "secret-123" not in payload
    assert "secret-password" not in payload
    assert "postgresql://" not in payload
    assert "safe_status" in payload


@pytest.mark.asyncio
async def test_ws21_8_learner_content_is_not_exposed():

    learner_message = (
        "Bonjour, ceci est un message "
        "confidentiel du learner."
    )

    service = (
        OperationalHealthSnapshotService(
            readiness_service=(
                make_readiness_service()
            )
        )
    )

    event = OperationalEvent(
        event_type=(
            OperationalEventType.MESSAGE_FAILURE
        ),
        surface=(
            OperationalSurface.PRIVATE_CLASSROOM
        ),
        correlation_id="message-001",
        metadata={
            "message": learner_message,
            "error_type": "TimeoutError",
        },
    )

    snapshot = await service.create_snapshot(
        events=(event,)
    )

    payload = str(
        snapshot.as_dict()
    )

    assert learner_message not in payload
    assert '"message"' not in payload.lower()


@pytest.mark.asyncio
async def test_ws21_8_identity_resolution_failure_is_safe():

    class BrokenResolver:

        async def resolve(
            self,
            user_reference: str,
        ):
            raise RuntimeError(
                "database password=SECRET"
            )

    service = (
        OperationalHealthSnapshotService(
            readiness_service=(
                make_readiness_service()
            ),
            identity_resolver=BrokenResolver(),
        )
    )

    event = OperationalEvent(
        event_type=(
            OperationalEventType.MESSAGE_FAILURE
        ),
        surface=(
            OperationalSurface.PRIVATE_CLASSROOM
        ),
        correlation_id="identity-001",
        user_reference="user-001",
    )

    snapshot = await service.create_snapshot(
        events=(event,)
    )

    assert len(snapshot.events) == 1

    payload = str(
        snapshot.as_dict()
    ).lower()

    assert "password" not in payload
    assert "secret" not in payload


@pytest.mark.asyncio
async def test_ws21_8_dashboard_contract_is_serializable():

    service = (
        OperationalHealthSnapshotService(
            readiness_service=(
                make_readiness_service()
            )
        )
    )

    snapshot = await service.create_snapshot()

    payload = snapshot.as_dict()

    assert set(payload) == {
        "generated_at",
        "overall_status",
        "ready",
        "dependency_health",
        "events",
        "private_classroom_events",
        "announcement_group_events",
    }

    assert isinstance(
        payload["dependency_health"],
        dict,
    )

    assert isinstance(
        payload["events"],
        list,
    )