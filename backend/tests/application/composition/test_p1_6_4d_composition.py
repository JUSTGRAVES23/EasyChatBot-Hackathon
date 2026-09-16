"""
P1.6.4D Operations Center composition contract tests.

Protects the Operations Center composition boundary for provider-usage
dashboard wiring.

The composition must:
- remain infrastructure-agnostic;
- accept ProviderUsageDashboardService through dependency injection;
- wire the injected service into the Operations Center composition;
- remain constructible without requiring database configuration.
"""

from __future__ import annotations

from unittest.mock import Mock

from app.application.operations_center.dashboard_composition import (
    create_operations_center_composition,
)
from app.application.provider_management.provider_usage_dashboard_service import (
    ProviderUsageDashboardService,
)


def test_p1_6_4d_default_composition_is_constructible_without_database_configuration(
    monkeypatch,
) -> None:
    """Operations Center composition must not create its own database infrastructure."""

    monkeypatch.delenv("DATABASE_URL", raising=False)

    composition = create_operations_center_composition()

    assert composition is not None


def test_p1_6_4d_injected_provider_usage_dashboard_service_is_preserved() -> None:
    """The injected provider-usage dashboard service must remain part of the composition."""

    provider_usage_dashboard_service = Mock(
        spec=ProviderUsageDashboardService,
    )

    composition = create_operations_center_composition(
        provider_usage_dashboard_service=provider_usage_dashboard_service,
    )

    assert (
        composition.provider_usage_dashboard_service
        is provider_usage_dashboard_service
    )


def test_p1_6_4d_composition_has_no_database_infrastructure_attributes() -> None:
    """Database infrastructure must remain owned by application bootstrap."""

    composition = create_operations_center_composition()

    assert not hasattr(composition, "provider_usage_engine")
    assert not hasattr(composition, "provider_usage_session_factory")
    assert not hasattr(composition, "provider_usage_repository")


