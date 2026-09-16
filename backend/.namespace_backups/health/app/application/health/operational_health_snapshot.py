from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Protocol

from .health_result import (
    HealthStatus,
    ProductionReadinessResult,
)
from .operational_event import (
    OperationalEvent,
    OperationalEventType,
    OperationalSurface,
    OperationalSeverity,
)


class TelegramIdentityResolver(Protocol):
    """
    Controlled application boundary for Telegram identity resolution.
    """

    async def resolve(
        self,
        user_reference: str,
    ) -> str | None:
        ...


@dataclass(frozen=True)
class OperationalHealthSnapshot:
    """
    Complete dashboard-safe operational snapshot.
    """

    generated_at: datetime
    overall_status: HealthStatus
    ready: bool

    dependency_health: dict[str, dict[str, Any]]

    events: tuple[OperationalEvent, ...]

    private_classroom_events: tuple[
        OperationalEvent,
        ...
    ]

    announcement_group_events: tuple[
        OperationalEvent,
        ...
    ]

    @property
    def postgresql_status(self) -> HealthStatus:
        return self._dependency_status("postgresql")

    @property
    def llm_status(self) -> HealthStatus:
        return self._dependency_status("llm_provider")

    @property
    def telegram_status(self) -> HealthStatus:
        return self._dependency_status("telegram")

    def _dependency_status(
        self,
        name: str,
    ) -> HealthStatus:
        value = self.dependency_health.get(name)

        if value is None:
            return HealthStatus.UNHEALTHY

        raw_status = value.get(
            "status",
            HealthStatus.UNHEALTHY.value,
        )

        try:
            return HealthStatus(raw_status)
        except ValueError:
            return HealthStatus.UNHEALTHY

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "overall_status": self.overall_status.value,
            "ready": self.ready,
            "dependency_health": {
                name: dict(details)
                for name, details
                in self.dependency_health.items()
            },
            "events": [
                _event_to_dict(event)
                for event in self.events
            ],
            "private_classroom_events": [
                _event_to_dict(event)
                for event in self.private_classroom_events
            ],
            "announcement_group_events": [
                _event_to_dict(event)
                for event in self.announcement_group_events
            ],
        }


class OperationalHealthSnapshotService:
    """
    Produces the complete operational health snapshot.
    """

    _SECRET_PATTERN = re.compile(
        r"(?i)"
        r"(password|passwd|secret|api[_-]?key|"
        r"access[_-]?token|refresh[_-]?token|"
        r"authorization|database[_-]?url|"
        r"telegram[_-]?bot[_-]?token)"
        r"\s*[:=]\s*"
        r"[^,\s;]+"
    )

    _SENSITIVE_KEY_PATTERN = re.compile(
        r"(?i)"
        r"password|passwd|secret|api[_-]?key|"
        r"access[_-]?token|refresh[_-]?token|"
        r"authorization|database[_-]?url|"
        r"bot[_-]?token|message|prompt|response"
    )

    def __init__(
        self,
        *,
        readiness_service,
        identity_resolver: (
            TelegramIdentityResolver | None
        ) = None,
    ) -> None:
        if readiness_service is None:
            raise ValueError(
                "readiness_service cannot be None."
            )

        self._readiness_service = readiness_service
        self._identity_resolver = identity_resolver

    async def create_snapshot(
        self,
        *,
        events: tuple[OperationalEvent, ...] = (),
    ) -> OperationalHealthSnapshot:

        readiness = await self._readiness_service.check()

        sanitized_events: list[OperationalEvent] = []

        for event in events:
            sanitized_event = await self._sanitize_event(event)
            sanitized_events.append(sanitized_event)

        private_events = tuple(
            event
            for event in sanitized_events
            if event.surface
            is OperationalSurface.PRIVATE_CLASSROOM
        )

        announcement_events = tuple(
            event
            for event in sanitized_events
            if event.surface
            is OperationalSurface.ANNOUNCEMENT_GROUP
        )

        dependency_health = (
            self._sanitize_dependency_health(readiness)
        )

        return OperationalHealthSnapshot(
            generated_at=datetime.now(timezone.utc),
            overall_status=readiness.status,
            ready=readiness.ready,
            dependency_health=dependency_health,
            events=tuple(sanitized_events),
            private_classroom_events=private_events,
            announcement_group_events=announcement_events,
        )

    async def _sanitize_event(
        self,
        event: OperationalEvent,
    ) -> OperationalEvent:

        user_reference = event.user_reference

        if user_reference and self._identity_resolver:
            try:
                resolved = await self._identity_resolver.resolve(
                    user_reference
                )
            except Exception:
                resolved = None

            if resolved:
                user_reference = resolved

        sanitized_metadata = self._sanitize_metadata(
            event.metadata
        )

        return OperationalEvent(
            event_type=event.event_type,
            surface=event.surface,
            correlation_id=self._sanitize_identifier(
                event.correlation_id
            ),
            severity=event.severity,
            occurred_at=event.occurred_at,
            user_reference=(
                self._sanitize_identifier(user_reference)
                if user_reference
                else None
            ),
            world_id=(
                self._sanitize_identifier(event.world_id)
                if event.world_id
                else None
            ),
            metadata=sanitized_metadata,
        )

    def _sanitize_dependency_health(
        self,
        readiness: ProductionReadinessResult,
    ) -> dict[str, dict[str, Any]]:

        result: dict[str, dict[str, Any]] = {}

        for check in readiness.checks:
            details = self._sanitize_metadata(
                check.details
            )

            result[
                self._sanitize_identifier(check.name)
            ] = {
                "status": check.status.value,
                "details": details,
            }

        return result

    def _sanitize_metadata(
        self,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:

        sanitized: dict[str, Any] = {}

        for key, value in metadata.items():

            if self._SENSITIVE_KEY_PATTERN.search(
                str(key)
            ):
                continue

            sanitized[
                self._sanitize_identifier(str(key))
            ] = self._sanitize_value(value)

        return sanitized

    def _sanitize_value(
        self,
        value: Any,
    ) -> Any:

        if isinstance(value, dict):
            return self._sanitize_metadata(value)

        if isinstance(value, (list, tuple)):
            return [
                self._sanitize_value(item)
                for item in value
            ]

        if isinstance(value, str):
            sanitized = self._SECRET_PATTERN.sub(
                "[REDACTED]",
                value,
            )

            if len(sanitized) > 500:
                return sanitized[:500] + "..."

            return sanitized

        if isinstance(value, (int, float, bool)):
            return value

        return str(value)

    @staticmethod
    def _sanitize_identifier(value: str) -> str:
        return (
            str(value)
            .replace("\r", "")
            .replace("\n", "")
            .strip()
        )


def _event_to_dict(
    event: OperationalEvent,
) -> dict[str, Any]:

    return {
        "event_type": event.event_type.value,
        "surface": event.surface.value,
        "correlation_id": event.correlation_id,
        "severity": event.severity.value,
        "occurred_at": event.occurred_at.isoformat(),
        "user_reference": event.user_reference,
        "world_id": event.world_id,
        "metadata": dict(event.metadata),
    }


__all__ = [
    "OperationalEvent",
    "OperationalEventType",
    "OperationalSeverity",
    "OperationalHealthSnapshot",
    "OperationalHealthSnapshotService",
    "OperationalSurface",
    "TelegramIdentityResolver",
]

