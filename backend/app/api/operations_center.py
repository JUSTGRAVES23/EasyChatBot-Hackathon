from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies.authorization import require_permission
from app.application.operations_center.dashboard_composition import (
    OperationsCenterComposition,
    create_operations_center_composition,
)
from app.application.operations_center.platform_intelligence_review_api import (
    PlatformIntelligenceReviewNotConfigured,
)
from app.application.provider_management.environment import (
    OperationsEnvironment,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from app.domain.authorization.permissions import Permission
from app.domain.identity.principal import Principal


class FunctionalityStopRequest(BaseModel):
    environment: OperationsEnvironment
    reason: str = Field(min_length=1, max_length=2000)


class FunctionalityResumeRequest(BaseModel):
    environment: OperationsEnvironment


def _control_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Functionality operational control is not configured.",
    )


def _result_as_dict(result: Any) -> dict[str, Any]:
    return {
        "functionality_id": result.functionality_id,
        "environment": result.environment,
        "availability": result.availability,
        "action": result.action,
        "reason": result.reason,
        "changed_at": result.changed_at.isoformat(),
        "changed_by": result.changed_by,
    }


def create_operations_center_router(
    *,
    composition: OperationsCenterComposition | None = None,
) -> APIRouter:
    resolved_composition = composition or create_operations_center_composition()

    dashboard_api = resolved_composition.dashboard_api
    chat_operations_api = resolved_composition.chat_operations_api
    functionality_health_service = resolved_composition.functionality_health_service
    functionality_control_service = (
        resolved_composition.functionality_control_service
    )
    event_service = resolved_composition.event_service
    provider_usage_dashboard_service = (
        resolved_composition.provider_usage_dashboard_service
    )
    platform_intelligence_review_api = (
        resolved_composition.platform_intelligence_review_api
    )

    router = APIRouter(
        prefix="/api/operations-center",
        tags=["operations-center"],
    )

    @router.get("/dashboard")
    async def get_dashboard() -> dict[str, Any]:
        return await dashboard_api.get_dashboard()

    @router.get("/chat-operations")
    async def get_chat_operations_dashboard() -> dict[str, Any]:
        return await chat_operations_api.get_dashboard()

    @router.get("/chat-operations/private-classroom")
    async def get_private_classroom_operations() -> dict[str, Any]:
        return await chat_operations_api.get_private_classroom_details()

    @router.get("/chat-operations/announcement-group")
    async def get_announcement_group_operations() -> dict[str, Any]:
        return await chat_operations_api.get_announcement_group_details()

    @router.get("/functionality-health")
    async def get_functionality_health(
        environment: OperationsEnvironment | None = None,
    ) -> dict[str, Any]:
        return await functionality_health_service.get_health(
            environment=environment
        )

    @router.post(
        "/functionality/{functionality_id}/stop",
        dependencies=[Depends(require_permission(Permission.FUNCTIONALITY_CONTROL))],
    )
    def stop_functionality(
        functionality_id: str,
        request: FunctionalityStopRequest,
        principal: Principal = Depends(
            require_permission(Permission.FUNCTIONALITY_CONTROL)
        ),
    ) -> dict[str, Any]:
        if functionality_control_service is None:
            raise _control_unavailable()

        try:
            result = functionality_control_service.stop(
                actor=principal,
                actor_name=principal.user_id,
                environment=request.environment.value,
                functionality_id=functionality_id,
                reason=request.reason,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission.",
            ) from None

        return _result_as_dict(result)

    @router.post(
        "/functionality/{functionality_id}/resume",
        dependencies=[Depends(require_permission(Permission.FUNCTIONALITY_CONTROL))],
    )
    def resume_functionality(
        functionality_id: str,
        request: FunctionalityResumeRequest,
        principal: Principal = Depends(
            require_permission(Permission.FUNCTIONALITY_CONTROL)
        ),
    ) -> dict[str, Any]:
        if functionality_control_service is None:
            raise _control_unavailable()

        try:
            result = functionality_control_service.resume(
                actor=principal,
                actor_name=principal.user_id,
                environment=request.environment.value,
                functionality_id=functionality_id,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission.",
            ) from None

        return _result_as_dict(result)



    @router.get(
        "/platform-intelligence/reviews",
        dependencies=[Depends(require_permission(Permission.INTERNAL_DATA_READ))],
    )
    def get_platform_intelligence_reviews() -> dict[str, Any]:
        try:
            return platform_intelligence_review_api.list_reviews()
        except PlatformIntelligenceReviewNotConfigured as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from None

    @router.get(
        "/platform-intelligence/reviews/{review_item_id}",
        dependencies=[Depends(require_permission(Permission.INTERNAL_DATA_READ))],
    )
    def get_platform_intelligence_review(
        review_item_id: str,
    ) -> dict[str, Any]:
        try:
            result = platform_intelligence_review_api.get_review(review_item_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from None
        except PlatformIntelligenceReviewNotConfigured as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from None
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform Intelligence review item not found.",
            )
        return result

    @router.get(
        "/platform-intelligence/escalations",
        dependencies=[Depends(require_permission(Permission.INTERNAL_DATA_READ))],
    )
    def get_platform_intelligence_escalations() -> dict[str, Any]:
        try:
            return platform_intelligence_review_api.list_escalations()
        except PlatformIntelligenceReviewNotConfigured as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from None

    @router.get("/operational-events")
    def get_operational_events() -> list[dict[str, Any]]:
        incidents = event_service.list_incidents()
        return [
            event.as_dict()
            for incident in incidents
            for event in incident.events
        ]

    @router.get("/provider-usage")
    def get_provider_usage() -> dict[str, Any]:
        if provider_usage_dashboard_service is None:
            return {
                "status": "not_configured",
                "reason": "provider_usage_dashboard_service_not_configured",
            }
        return provider_usage_dashboard_service.get_snapshot()

    return router


router = create_operations_center_router()

__all__ = ["router", "create_operations_center_router"]


