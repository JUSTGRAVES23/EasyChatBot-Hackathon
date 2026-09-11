"""
Project Control Center production composition.

This module assembles the Project Control Center application service
from authoritative application-layer dependencies.

Responsibilities:

- construct the approved PCD source adapters;
- inject authoritative application services/registries;
- construct ProjectControlService.

This module does NOT:

- own authoritative project state;
- duplicate Health state;
- duplicate Operations state;
- duplicate Privacy Governance state;
- call providers directly;
- mutate production systems;
- execute project-management decisions.

Architecture:

    Authoritative Application Services / Registries
                         |
                         v
                 PCD Source Adapters
                         |
                         v
                ProjectControlService
                         |
                         v
                ProjectControlSnapshot
"""

from __future__ import annotations

from app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from app.application.health.production_health_service import (
    ProductionHealthService,
)
from app.application.privacy.privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)

from ..application.service import ProjectControlService
from ..domain.ports import ProjectRegistry, SnapshotRepository
from .governance_risk_source import (
    GovernanceRiskProjectStatusSource,
)
from .health_source import (
    ProductionHealthProjectStatusSource,
)
from .operations_source import (
    OperationsProjectStatusSource,
)


def create_project_control_service(
    *,
    registry: ProjectRegistry,
    snapshots: SnapshotRepository,
    health_service: ProductionHealthService,
    dashboard_service: OperationalDashboardService,
    case_registry: PrivacyGovernanceCaseRegistry,
) -> ProjectControlService:
    """
    Create the production ProjectControlService.

    All dependencies are supplied explicitly.

    The function constructs only the PCD read-only adapters. The
    authoritative application services and registries remain owned
    by their respective bounded contexts.

    Args:
        registry:
            Authoritative PCD project registry.

        snapshots:
            PCD snapshot repository.

        health_service:
            Existing ProductionHealthService.

        dashboard_service:
            Existing OperationalDashboardService.

        case_registry:
            Existing PrivacyGovernanceCaseRegistry.

    Returns:
        Fully composed ProjectControlService.

    Raises:
        ValueError:
            If a required dependency is None.
    """

    if registry is None:
        raise ValueError(
            "registry cannot be None."
        )

    if snapshots is None:
        raise ValueError(
            "snapshots cannot be None."
        )

    if health_service is None:
        raise ValueError(
            "health_service cannot be None."
        )

    if dashboard_service is None:
        raise ValueError(
            "dashboard_service cannot be None."
        )

    if case_registry is None:
        raise ValueError(
            "case_registry cannot be None."
        )

    health_source = ProductionHealthProjectStatusSource(
        health_service=health_service,
    )

    operations_source = OperationsProjectStatusSource(
        dashboard_service=dashboard_service,
    )

    governance_source = GovernanceRiskProjectStatusSource(
        case_registry=case_registry,
    )

    return ProjectControlService(
        registry=registry,
        sources=(
            health_source,
            operations_source,
            governance_source,
        ),
        snapshots=snapshots,
    )


__all__ = [
    "create_project_control_service",
]
