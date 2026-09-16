from __future__ import annotations

from fastapi import APIRouter, Request

from app.application.operations_center.email_workflow_status_service import (
    EmailWorkflowStatusService,
)
from cybersecurity.email.email_provider_manager import EmailProviderManager


def create_email_workflows_router() -> APIRouter:
    router = APIRouter(
        prefix="/api/operations-center/email-workflows",
        tags=["Operations Center", "Email Workflows"],
    )

    @router.get("")
    async def get_email_workflows(request: Request):
        service = EmailWorkflowStatusService(
            scheduler_runtime=request.app.state.scheduler_runtime,
            provider_manager=EmailProviderManager(),
        )
        return service.snapshot()

    return router


__all__ = ["create_email_workflows_router"]

