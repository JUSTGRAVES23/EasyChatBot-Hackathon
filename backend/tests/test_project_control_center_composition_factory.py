from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from app.application.health.production_health_service import (
    ProductionHealthService,
)
from app.application.privacy.privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)
from app.project_control_center.application.service import (
    ProjectControlService,
)
from app.project_control_center.domain.models import (
    ProjectDefinition,
)
from app.project_control_center.domain.ports import (
    ProjectRegistry,
    SnapshotRepository,
)
from app.project_control_center.infrastructure.composition import (
    create_project_control_service,
)
from app.project_control_center.infrastructure.governance_risk_source import (
    GovernanceRiskProjectStatusSource,
)
from app.project_control_center.infrastructure.health_source import (
    ProductionHealthProjectStatusSource,
)
from app.project_control_center.infrastructure.in_memory import (
    InMemoryProjectRegistry,
    InMemorySnapshotRepository,
)
from app.project_control_center.infrastructure.operations_source import (
    OperationsProjectStatusSource,
)


@dataclass
class FakeProductionHealthService:
    """Minimal dependency for composition testing."""


@dataclass
class FakeDashboardService:
    """Minimal dependency for composition testing."""


def make_dependencies():
    registry = InMemoryProjectRegistry()

    registry.save(
        ProjectDefinition(
            project_id="easychatbot",
            name="EasyChatBot",
        )
    )

    snapshots = InMemorySnapshotRepository()
    health_service = FakeProductionHealthService()
    dashboard_service = FakeDashboardService()
    case_registry = PrivacyGovernanceCaseRegistry()

    return (
        registry,
        snapshots,
        health_service,
        dashboard_service,
        case_registry,
    )


def test_factory_returns_project_control_service():
    (
        registry,
        snapshots,
        health_service,
        dashboard_service,
        case_registry,
    ) = make_dependencies()

    service = create_project_control_service(
        registry=registry,
        snapshots=snapshots,
        health_service=health_service,
        dashboard_service=dashboard_service,
        case_registry=case_registry,
    )

    assert isinstance(
        service,
        ProjectControlService,
    )


def test_factory_registers_expected_source_adapters():
    (
        registry,
        snapshots,
        health_service,
        dashboard_service,
        case_registry,
    ) = make_dependencies()

    service = create_project_control_service(
        registry=registry,
        snapshots=snapshots,
        health_service=health_service,
        dashboard_service=dashboard_service,
        case_registry=case_registry,
    )

    assert len(service.sources) == 3

    assert isinstance(
        service.sources[0],
        ProductionHealthProjectStatusSource,
    )

    assert isinstance(
        service.sources[1],
        OperationsProjectStatusSource,
    )

    assert isinstance(
        service.sources[2],
        GovernanceRiskProjectStatusSource,
    )


def test_factory_preserves_source_order():
    (
        registry,
        snapshots,
        health_service,
        dashboard_service,
        case_registry,
    ) = make_dependencies()

    service = create_project_control_service(
        registry=registry,
        snapshots=snapshots,
        health_service=health_service,
        dashboard_service=dashboard_service,
        case_registry=case_registry,
    )

    assert [
        source.source_id
        for source in service.sources
    ] == [
        "production-health",
        "operations-center",
        "privacy-governance",
    ]


def test_factory_injects_existing_authoritative_dependencies():
    (
        registry,
        snapshots,
        health_service,
        dashboard_service,
        case_registry,
    ) = make_dependencies()

    service = create_project_control_service(
        registry=registry,
        snapshots=snapshots,
        health_service=health_service,
        dashboard_service=dashboard_service,
        case_registry=case_registry,
    )

    assert service.sources[0]._health_service is health_service
    assert service.sources[1]._dashboard_service is dashboard_service
    assert service.sources[2]._case_registry is case_registry


def test_factory_preserves_project_registry():
    (
        registry,
        snapshots,
        health_service,
        dashboard_service,
        case_registry,
    ) = make_dependencies()

    service = create_project_control_service(
        registry=registry,
        snapshots=snapshots,
        health_service=health_service,
        dashboard_service=dashboard_service,
        case_registry=case_registry,
    )

    assert service.registry is registry


def test_factory_preserves_snapshot_repository():
    (
        registry,
        snapshots,
        health_service,
        dashboard_service,
        case_registry,
    ) = make_dependencies()

    service = create_project_control_service(
        registry=registry,
        snapshots=snapshots,
        health_service=health_service,
        dashboard_service=dashboard_service,
        case_registry=case_registry,
    )

    assert service.snapshots is snapshots


@pytest.mark.parametrize(
    "argument",
    [
        "registry",
        "snapshots",
        "health_service",
        "dashboard_service",
        "case_registry",
    ],
)
def test_factory_rejects_missing_required_dependency(argument):
    (
        registry,
        snapshots,
        health_service,
        dashboard_service,
        case_registry,
    ) = make_dependencies()

    dependencies = {
        "registry": registry,
        "snapshots": snapshots,
        "health_service": health_service,
        "dashboard_service": dashboard_service,
        "case_registry": case_registry,
    }

    dependencies[argument] = None

    with pytest.raises(
        ValueError,
        match=f"{argument} cannot be None",
    ):
        create_project_control_service(
            **dependencies,
        )


def test_factory_does_not_create_duplicate_authoritative_stores():
    (
        registry,
        snapshots,
        health_service,
        dashboard_service,
        case_registry,
    ) = make_dependencies()

    service = create_project_control_service(
        registry=registry,
        snapshots=snapshots,
        health_service=health_service,
        dashboard_service=dashboard_service,
        case_registry=case_registry,
    )

    assert service.sources[0]._health_service is health_service
    assert service.sources[1]._dashboard_service is dashboard_service
    assert service.sources[2]._case_registry is case_registry

    assert not hasattr(
        service,
        "health_state",
    )

    assert not hasattr(
        service,
        "operations_state",
    )

    assert not hasattr(
        service,
        "privacy_state",
    )