from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.application.persistence_operations import PersistenceDiagnosticsService


def create_persistence_operations_router(
    service: PersistenceDiagnosticsService,
    *,
    operator_dependency: Callable[..., Any],
) -> APIRouter:
    router = APIRouter(prefix="/api/operations-center/persistence", tags=["operations-center-persistence"])

    @router.get("", summary="Get live persistence overview")
    def get_persistence_diagnostics(
        environment: str = Query("dev", pattern="^(dev|staging|production)$"),
        _operator: Any = Depends(operator_dependency),
    ) -> dict[str, Any]:
        return service.snapshot(environment=environment)

    @router.get("/health", summary="Get live PostgreSQL health and operations")
    def get_database_health(
        environment: str = Query("dev", pattern="^(dev|staging|production)$"),
        _operator: Any = Depends(operator_dependency),
    ) -> dict[str, Any]:
        return service.health_snapshot(environment=environment)

    return router

