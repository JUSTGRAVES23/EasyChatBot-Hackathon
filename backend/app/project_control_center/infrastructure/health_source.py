from __future__ import annotations

from datetime import datetime, timezone

from app.application.health.health_result import HealthStatus
from app.application.health.production_health_service import (
    ProductionHealthService,
)

from ..domain.models import (
    ActionSnapshot,
    IssueSnapshot,
    MetricSnapshot,
    MilestoneSnapshot,
    RiskSnapshot,
    SourceSnapshot,
    SourceStatus,
    WorkstreamSnapshot,
)
from ..domain.ports import ProjectStatusSource


class ProductionHealthProjectStatusSource(ProjectStatusSource):
    """Read-only PCD adapter over ProductionHealthService.

    This adapter does not access databases, Telegram, LLM providers,
    or infrastructure health checks directly.

    ProductionHealthService remains the authoritative application-level
    entry point for production health.

    PCD-2A integrates health only. It deliberately does not invent or
    duplicate project workstream, issue, risk, action, or milestone data.
    """

    _SOURCE_ID = "production-health"
    _SOURCE_NAME = "Production Health"

    def __init__(
        self,
        *,
        health_service: ProductionHealthService,
    ) -> None:
        if health_service is None:
            raise ValueError(
                "health_service cannot be None."
            )

        self._health_service = health_service

    @property
    def source_id(self) -> str:
        return self._SOURCE_ID

    @property
    def source_name(self) -> str:
        return self._SOURCE_NAME

    def health(self) -> SourceSnapshot:
        """Report adapter availability without probing dependencies.

        ProjectStatusSource.health() is synchronous, while the real
        production health check is asynchronous. Therefore this method
        intentionally performs no external health probe.

        The actual production health result is obtained through
        fetch_health().
        """
        return SourceSnapshot(
            source_id=self.source_id,
            name=self.source_name,
            status=SourceStatus.AVAILABLE,
            updated_at=datetime.now(timezone.utc),
        )

    async def fetch_health(self) -> SourceSnapshot:
        """Execute ProductionHealthService and translate its result."""
        try:
            result = (
                await self._health_service
                .check_production_health()
            )
        except Exception:
            return SourceSnapshot(
                source_id=self.source_id,
                name=self.source_name,
                status=SourceStatus.UNAVAILABLE,
                updated_at=datetime.now(timezone.utc),
                error="production_health_check_failed",
            )

        if result.status is HealthStatus.HEALTHY:
            return SourceSnapshot(
                source_id=self.source_id,
                name=self.source_name,
                status=SourceStatus.AVAILABLE,
                updated_at=datetime.now(timezone.utc),
            )

        return SourceSnapshot(
            source_id=self.source_id,
            name=self.source_name,
            status=SourceStatus.UNAVAILABLE,
            updated_at=datetime.now(timezone.utc),
            error="production_health_not_ready",
        )

    async def fetch_metrics(
        self,
        project_id: str,
    ) -> list[MetricSnapshot]:
        """PCD-2A does not create project metrics."""
        return []

    def fetch_workstreams(
        self,
        project_id: str,
    ) -> list[WorkstreamSnapshot]:
        """PCD-2A does not create project workstream data."""
        return []

    def fetch_issues(
        self,
        project_id: str,
    ) -> list[IssueSnapshot]:
        """PCD-2A does not create project issue data."""
        return []

    def fetch_risks(
        self,
        project_id: str,
    ) -> list[RiskSnapshot]:
        """PCD-2A does not create project risk data."""
        return []

    def fetch_actions(
        self,
        project_id: str,
    ) -> list[ActionSnapshot]:
        """PCD-2A does not create project action data."""
        return []

    def fetch_milestones(
        self,
        project_id: str,
    ) -> list[MilestoneSnapshot]:
        """PCD-2A does not create project milestone data."""
        return []


__all__ = [
    "ProductionHealthProjectStatusSource",
]
