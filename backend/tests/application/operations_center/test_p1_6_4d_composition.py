from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import Mock

from app.application.operations_center.dashboard_composition import (
    OperationsCenterComposition,
)
from app.application.provider_management.provider_usage_dashboard_service import (
    ProviderUsageDashboardService,
)


def test_operations_center_composition_accepts_usage_service_without_database_creation(
    monkeypatch,
):
    import app.application.operations_center.dashboard_composition as module

    def fail_database_creation():
        raise AssertionError(
            "Operations Center composition must not create a database engine."
        )

    monkeypatch.setattr(module, "create_database_engine", fail_database_creation, raising=False)

    service = Mock(spec=ProviderUsageDashboardService)

    composition = OperationsCenterComposition(
        provider_usage_dashboard_service=service,
    )

    assert composition.provider_usage_dashboard_service is service


def test_operations_center_router_can_be_composed_with_injected_usage_service():
    import app.api.operations_center as module

    service = Mock(spec=ProviderUsageDashboardService)
    composition = OperationsCenterComposition(
        provider_usage_dashboard_service=service,
    )

    router = module.create_operations_center_router(composition=composition)

    paths = {route.path for route in router.routes}

    assert "/api/operations-center/provider-usage" in paths
    assert "/api/operations-center/dashboard" in paths
    assert "/api/operations-center/functionality-health" in paths


def test_importing_operations_center_module_does_not_require_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    sys.modules.pop("backend.app.api.operations_center", None)

    module = importlib.import_module("backend.app.api.operations_center")

    assert module.router is not None

