from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.application.operations_center.email_workflow_status_service import (
    EmailWorkflowStatusService,
)
from app.infrastructure.persistence.postgresql_email_workflow_registry import (
    PostgreSQLEmailWorkflowRegistry,
)
from cybersecurity.email.email_provider_manager import EmailProviderManager


def create_email_workflows_router(
    *,
    session_factory,
    operator_dependency: Callable[..., Any],
) -> APIRouter:
    if session_factory is None:
        raise ValueError("session_factory is required.")
    if operator_dependency is None:
        raise ValueError("operator_dependency is required.")

    registry = PostgreSQLEmailWorkflowRegistry(session_factory)

    router = APIRouter(
        prefix="/api/operations-center/email-workflows",
        tags=["Operations Center", "Email Workflows"],
    )

    @router.get("")
    async def get_email_workflows(
        request: Request,
        _operator: Any = Depends(operator_dependency),
    ):
        service = EmailWorkflowStatusService(
            scheduler_runtime=request.app.state.scheduler_runtime,
            provider_manager=EmailProviderManager(),
            registry=registry,
        )
        return service.snapshot()

    @router.get("/{workflow_id}")
    async def get_email_workflow(
        workflow_id: str,
        request: Request,
        _operator: Any = Depends(operator_dependency),
    ):
        service = EmailWorkflowStatusService(
            scheduler_runtime=request.app.state.scheduler_runtime,
            provider_manager=EmailProviderManager(),
            registry=registry,
        )
        workflow = service.get(workflow_id)

        if workflow is None:
            raise HTTPException(
                status_code=404,
                detail="Email workflow not found.",
            )

        return workflow

    return router
