from __future__ import annotations

from unittest.mock import Mock

from app.application.operations_center.dashboard_composition import (
    create_operations_center_composition,
)
from app.application.provider_management.provider_usage_dashboard_service import (
    ProviderUsageDashboardService,
)
from app.api.operations_center import (
    create_operations_center_router,
)


def test_production_operations_center_composition_receives_usage_service():
    service = Mock(spec=ProviderUsageDashboardService)

    composition = create_operations_center_composition(
        provider_usage_dashboard_service=service,
    )

    assert composition.provider_usage_dashboard_service is service


def test_production_operations_center_router_exposes_provider_usage():
    service = Mock(spec=ProviderUsageDashboardService)

    composition = create_operations_center_composition(
        provider_usage_dashboard_service=service,
    )

    router = create_operations_center_router(
        composition=composition,
    )

    paths = {route.path for route in router.routes}

    assert "/api/operations-center/provider-usage" in paths
    assert "/api/operations-center/dashboard" in paths
    assert "/api/operations-center/functionality-health" in paths
    assert "/api/operations-center/operational-events" in paths

