from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.api.dependencies.authorization import require_permission
from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminLastAdminError,
    DeveloperAdminService,
    DeveloperAdminUserInactiveError,
    DeveloperAdminUserNotFoundError,
)
from app.domain.authorization.permissions import Permission
from app.domain.identity.principal import Principal


class DeveloperAdminGrantRequest(BaseModel):
    user_id: UUID


class DeveloperAdminResponse(BaseModel):
    user_id: UUID
    email: str
    username: str
    status: str
    email_verified: bool


class DeveloperAdminListResponse(BaseModel):
    administrators: list[DeveloperAdminResponse]


def _get_service(request: Request) -> DeveloperAdminService:
    service = getattr(request.app.state, "developer_admin_service", None)
    if service is None:
        raise RuntimeError("developer_admin_service is not configured.")
    return service


router = APIRouter(
    prefix="/api/operations-center/developer-administrators",
    tags=["operations-center-developer-administrators"],
)


@router.get("", response_model=DeveloperAdminListResponse)
async def list_developer_administrators(
    request: Request,
    _principal: Principal = Depends(
        require_permission(Permission.DEVELOPER_ADMIN_MANAGE)
    ),
) -> DeveloperAdminListResponse:
    administrators = await _get_service(request).list_developer_administrators()
    return DeveloperAdminListResponse(
        administrators=[
            DeveloperAdminResponse(
                user_id=item.user_id,
                email=item.email,
                username=item.username,
                status=item.status,
                email_verified=item.email_verified,
            )
            for item in administrators
        ]
    )


@router.post(
    "",
    response_model=DeveloperAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
async def grant_developer_admin(
    payload: DeveloperAdminGrantRequest,
    request: Request,
    principal: Principal = Depends(
        require_permission(Permission.DEVELOPER_ADMIN_MANAGE)
    ),
) -> DeveloperAdminResponse:
    try:
        administrator = await _get_service(request).grant_developer_admin(
            actor=principal,
            user_id=payload.user_id,
        )
    except DeveloperAdminUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except DeveloperAdminUserInactiveError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None

    return DeveloperAdminResponse(
        user_id=administrator.user_id,
        email=administrator.email,
        username=administrator.username,
        status=administrator.status,
        email_verified=administrator.email_verified,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_developer_admin(
    user_id: UUID,
    request: Request,
    principal: Principal = Depends(
        require_permission(Permission.DEVELOPER_ADMIN_MANAGE)
    ),
) -> None:
    try:
        await _get_service(request).revoke_developer_admin(
            actor=principal,
            user_id=user_id,
        )
    except DeveloperAdminUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except DeveloperAdminLastAdminError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
