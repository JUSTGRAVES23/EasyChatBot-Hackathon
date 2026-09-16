from __future__ import annotations

from datetime import datetime, timezone

from .health_result import HealthStatus
from .operational_dashboard_models import (
    DashboardDependencyStatus,
    DashboardIncident,
    DashboardIncidentSummary,
    DashboardOperationalMetrics,
    DashboardSurfaceStatus,
    OperationalDashboardSnapshot,
)
from .operational_event import OperationalEventType, OperationalSurface
from .operational_event_service import OperationalEventService
from .operational_health_snapshot import OperationalHealthSnapshotService


class OperationalDashboardService:
    """
    Application service producing the read-only operational dashboard.

    Dependency health is probed fresh for every snapshot.

    Incident/event state comes from the application-owned
    OperationalEventService.

    The event service is exposed through a read-only property so dependent
    Operations Center application APIs can explicitly reuse the same
    authoritative operational state.
    """

    def __init__(
        self,
        *,
        health_snapshot_service: OperationalHealthSnapshotService,
        event_service: OperationalEventService,
    ) -> None:
        if health_snapshot_service is None:
            raise ValueError(
                "health_snapshot_service cannot be None."
            )

        if event_service is None:
            raise ValueError(
                "event_service cannot be None."
            )

        self._health_snapshot_service = (
            health_snapshot_service
        )

        self._event_service = event_service

    @property
    def event_service(self) -> OperationalEventService:
        """
        Return the authoritative application-owned event service.

        This does not create a new service or event store.

        It allows dependent read-only Operations Center APIs to use the
        exact same operational state as this dashboard service.
        """
        return self._event_service

    async def create_dashboard_snapshot(
        self,
    ) -> OperationalDashboardSnapshot:
        """
        Create a fresh operational dashboard snapshot.

        Dependency health and current incident state are evaluated for
        every request.
        """

        health = (
            await self._health_snapshot_service.create_snapshot()
        )

        incidents = self._event_service.list_incidents()

        operational_events = tuple(
            event
            for incident in incidents
            for event in incident.events
        )

        dashboard_incidents = tuple(
            DashboardIncident.from_incident(
                incident
            )
            for incident in incidents
        )

        private_incidents = tuple(
            incident
            for incident in incidents
            if incident.surface
            is OperationalSurface.PRIVATE_CLASSROOM
        )

        announcement_incidents = tuple(
            incident
            for incident in incidents
            if incident.surface
            is OperationalSurface.ANNOUNCEMENT_GROUP
        )

        private_events = tuple(
            event
            for event in operational_events
            if event.surface
            is OperationalSurface.PRIVATE_CLASSROOM
        )

        announcement_events = tuple(
            event
            for event in operational_events
            if event.surface
            is OperationalSurface.ANNOUNCEMENT_GROUP
        )

        return OperationalDashboardSnapshot(
            generated_at=datetime.now(timezone.utc),
            overall_status=health.overall_status,
            health_score=self._calculate_health_score(
                health.overall_status,
                incidents,
            ),
            private_classroom=self._surface_status(
                health=health,
                surface=OperationalSurface.PRIVATE_CLASSROOM,
                incidents=private_incidents,
                events=private_events,
            ),
            announcement_group=self._surface_status(
                health=health,
                surface=OperationalSurface.ANNOUNCEMENT_GROUP,
                incidents=announcement_incidents,
                events=announcement_events,
            ),
            incidents=dashboard_incidents,
        )

    def list_incidents(
        self,
        *,
        surface: OperationalSurface | None = None,
    ):
        """
        Read current incidents through the existing operational-event
        abstraction.

        No second incident store is created.
        """

        return self._event_service.list_incidents(
            surface=surface
        )

    def _surface_status(
        self,
        *,
        health,
        surface: OperationalSurface,
        incidents,
        events,
    ) -> DashboardSurfaceStatus:
        return DashboardSurfaceStatus(
            surface=surface,
            status=self._surface_health_status(
                health=health,
                surface=surface,
                incidents=incidents,
            ),
            dependencies=self._dependency_statuses(
                health
            ),
            incidents=self._incident_summary(
                incidents
            ),
            metrics=self._operational_metrics(
                events
            ),
        )

    @staticmethod
    def _dependency_statuses(health):
        result = []

        for name, value in health.dependency_health.items():
            try:
                status = HealthStatus(
                    value.get(
                        "status",
                        HealthStatus.UNHEALTHY.value,
                    )
                )
            except ValueError:
                status = HealthStatus.UNHEALTHY

            result.append(
                DashboardDependencyStatus(
                    name=name,
                    status=status,
                    details=dict(
                        value.get(
                            "details",
                            {}
                        )
                    ),
                )
            )

        return tuple(result)

    @staticmethod
    def _incident_summary(incidents):
        return DashboardIncidentSummary(
            total=len(incidents),
            open=sum(
                incident.is_open
                for incident in incidents
            ),
            critical=sum(
                incident.severity.value == "critical"
                for incident in incidents
            ),
            high=sum(
                incident.severity.value == "high"
                for incident in incidents
            ),
            medium=sum(
                incident.severity.value == "medium"
                for incident in incidents
            ),
            low=sum(
                incident.severity.value == "low"
                for incident in incidents
            ),
            info=sum(
                incident.severity.value == "info"
                for incident in incidents
            ),
        )

    @staticmethod
    def _operational_metrics(events):
        return DashboardOperationalMetrics(
            message_failures=sum(
                event.event_type
                is OperationalEventType.MESSAGE_FAILURE
                for event in events
            ),
            rate_limit_events=sum(
                event.event_type
                is OperationalEventType.RATE_LIMIT
                for event in events
            ),
            abuse_events=sum(
                event.event_type
                is OperationalEventType.ABUSE
                for event in events
            ),
        )

    @staticmethod
    def _surface_health_status(
        *,
        health,
        surface,
        incidents,
    ):
        if any(
            incident.is_open
            and incident.severity.value
            in {"critical", "high"}
            for incident in incidents
        ):
            return HealthStatus.UNHEALTHY

        if surface is OperationalSurface.PRIVATE_CLASSROOM:
            statuses = (
                health.telegram_status,
                health.postgresql_status,
                health.llm_status,
            )
        else:
            statuses = (
                health.telegram_status,
            )

        if all(
            status is HealthStatus.HEALTHY
            for status in statuses
        ):
            return HealthStatus.HEALTHY

        return HealthStatus.UNHEALTHY

    @staticmethod
    def _calculate_health_score(
        overall_status,
        incidents,
    ) -> int:
        score = (
            100
            if overall_status is HealthStatus.HEALTHY
            else 60
        )

        critical_open = sum(
            incident.is_open
            and incident.severity.value == "critical"
            for incident in incidents
        )

        high_open = sum(
            incident.is_open
            and incident.severity.value == "high"
            for incident in incidents
        )

        score -= critical_open * 20
        score -= high_open * 10

        return max(
            0,
            min(100, score),
        )


__all__ = [
    "OperationalDashboardService",
]