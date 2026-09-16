from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.api.dependencies.authorization import require_permission
from app.api.routes.developer_admin_transaction_contracts import (
    DeveloperAdminApprovalResponse,
    DeveloperAdminCreateTransactionRequest,
    DeveloperAdminExecuteTransactionResponse,
    DeveloperAdminPendingTransactionResponse,
)
from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminLastAdminError,
    DeveloperAdminService,
    DeveloperAdminUserInactiveError,
    DeveloperAdminUserNotFoundError,
)
from app.application.developer_admin.developer_admin_transaction_service import (
    DeveloperAdminTransactionService,
)
from app.application.developer_admin.trusted_approval_provider import (
    TrustedApprovalRequest,
    TrustedApprovalUnavailableError,
    UnavailableTrustedApprovalProvider,
)
from app.application.identity.transaction_authorization import (
    TransactionAuthorizationApplicationError,
)
from app.domain.authorization.permissions import Permission
from app.domain.identity.principal import Principal


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


def _get_transaction_service(request: Request) -> DeveloperAdminTransactionService:
    service = getattr(request.app.state, "developer_admin_transaction_service", None)
    if service is None:
        raise RuntimeError("developer_admin_transaction_service is not configured.")
    return service


def _get_approval_provider(request: Request):
    return getattr(
        request.app.state,
        "developer_admin_trusted_approval_provider",
        UnavailableTrustedApprovalProvider(),
    )


router = APIRouter(
    prefix="/api/operations-center/developer-administrators",
    tags=["operations-center-developer-administrators"],
)


@router.get("")
async def list_developer_administrators(
    request: Request,
    _principal: Principal = Depends(
        require_permission(Permission.DEVELOPER_ADMIN_MANAGE)
    ),
):
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
    "/transactions/grant",
    response_model=DeveloperAdminPendingTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_grant_transaction(
    payload: DeveloperAdminCreateTransactionRequest,
    request: Request,
    principal: Principal = Depends(
        require_permission(Permission.DEVELOPER_ADMIN_MANAGE)
    ),
) -> DeveloperAdminPendingTransactionResponse:
    authorization = _get_transaction_service(request).create_grant_transaction(
        principal=principal,
        target_user_id=payload.target_user_id,
    )
    transaction = authorization.transaction
    target_user_id = UUID(dict(transaction.risk_context)["target_user_id"])
    return DeveloperAdminPendingTransactionResponse(
        authorization_id=authorization.authorization_id,
        transaction_id=transaction.transaction_id,
        operation=transaction.operation,
        audience=dict(transaction.risk_context)["audience"],
        target_user_id=target_user_id,
        state=authorization.state.value,
        expires_at=authorization.expires_at,
    )


@router.post(
    "/transactions/revoke",
    response_model=DeveloperAdminPendingTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_revoke_transaction(
    payload: DeveloperAdminCreateTransactionRequest,
    request: Request,
    principal: Principal = Depends(
        require_permission(Permission.DEVELOPER_ADMIN_MANAGE)
    ),
) -> DeveloperAdminPendingTransactionResponse:
    authorization = _get_transaction_service(request).create_revoke_transaction(
        principal=principal,
        target_user_id=payload.target_user_id,
    )
    transaction = authorization.transaction
    target_user_id = UUID(dict(transaction.risk_context)["target_user_id"])
    return DeveloperAdminPendingTransactionResponse(
        authorization_id=authorization.authorization_id,
        transaction_id=transaction.transaction_id,
        operation=transaction.operation,
        audience=dict(transaction.risk_context)["audience"],
        target_user_id=target_user_id,
        state=authorization.state.value,
        expires_at=authorization.expires_at,
    )


@router.post(
    "/transactions/{authorization_id}/approve",
    response_model=DeveloperAdminApprovalResponse,
)
async def approve_transaction(
    authorization_id: str,
    request: Request,
    principal: Principal = Depends(
        require_permission(Permission.DEVELOPER_ADMIN_MANAGE)
    ),
) -> DeveloperAdminApprovalResponse:
    transaction_service = _get_transaction_service(request)
    authorization = transaction_service.get_authorization(
        authorization_id=authorization_id
    )
    if authorization is None:
        raise HTTPException(status_code=404, detail="Transaction authorization was not found.")

    provider = _get_approval_provider(request)
    try:
        approval = await provider.approve(
            request=TrustedApprovalRequest(
                authorization_id=authorization.authorization_id,
                principal_id=principal.user_id,
                audience=transaction_service.AUDIENCE,
                transaction_id=authorization.transaction.transaction_id,
                requested_at=authorization.created_at,
            )
        )
        approved = transaction_service.attach_trusted_approval(
            principal=principal,
            approval=approval,
        )
    except TrustedApprovalUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except (PermissionError, TransactionAuthorizationApplicationError, ValueError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None

    return DeveloperAdminApprovalResponse(
        authorization_id=approved.authorization_id,
        transaction_id=approved.transaction.transaction_id,
        state=approved.state.value,
        expires_at=approved.expires_at,
    )


@router.post(
    "/transactions/{authorization_id}/execute",
    response_model=DeveloperAdminExecuteTransactionResponse,
)
async def execute_transaction(
    authorization_id: str,
    request: Request,
    principal: Principal = Depends(
        require_permission(Permission.DEVELOPER_ADMIN_MANAGE)
    ),
) -> DeveloperAdminExecuteTransactionResponse:
    transaction_service = _get_transaction_service(request)
    authorization = transaction_service.get_authorization(
        authorization_id=authorization_id
    )
    if authorization is None:
        raise HTTPException(status_code=404, detail="Transaction authorization was not found.")

    try:
        if authorization.transaction.operation == transaction_service.GRANT_OPERATION:
            await transaction_service.execute_grant(
                principal=principal,
                authorization_id=authorization_id,
            )
        elif authorization.transaction.operation == transaction_service.REVOKE_OPERATION:
            await transaction_service.execute_revoke(
                principal=principal,
                authorization_id=authorization_id,
            )
        else:
            raise PermissionError("Developer Administrator transaction operation is invalid.")
    except DeveloperAdminUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except (DeveloperAdminUserInactiveError, DeveloperAdminLastAdminError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except (PermissionError, TransactionAuthorizationApplicationError, ValueError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None

    consumed = transaction_service.get_authorization(
        authorization_id=authorization_id
    )
    state = consumed.state.value if consumed is not None else "CONSUMED"
    return DeveloperAdminExecuteTransactionResponse(
        authorization_id=authorization_id,
        state=state,
    )


__all__ = ["router"]
