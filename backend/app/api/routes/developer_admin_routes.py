from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

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


def _get_service(request: Request) -> DeveloperAdminService:
    service = getattr(request.app.state, "developer_admin_service", None)
    if service is None:
        raise RuntimeError("developer_admin_service is not configured.")
    return service


def _get_transaction_service(
    request: Request,
) -> DeveloperAdminTransactionService:
    service = getattr(
        request.app.state,
        "developer_admin_transaction_service",
        None,
    )
    if service is None:
        raise RuntimeError(
            "developer_admin_transaction_service is not configured."
        )
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

    return {
        "administrators": [
            {
                "user_id": item.user_id,
                "email": item.email,
                "username": item.username,
                "status": item.status,
                "email_verified": item.email_verified,
            }
            for item in administrators
        ]
    }


# ---------------------------------------------------------------------------
# Legacy collection mutation retirement boundary
#
# Direct Developer Administrator mutations are no longer supported.
#
# The only supported mutation path is:
#
#   create transaction
#       ->
#   trusted approval
#       ->
#   execute transaction
#
# This explicit POST tombstone exists only for the former collection
# mutation endpoint. It performs no mutation.
#
# The former DELETE /{user_id} endpoint intentionally does NOT exist.
# Keeping that route out of the router is part of the API contract.
# ---------------------------------------------------------------------------


@router.post("")
async def legacy_direct_create_developer_administrator() -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=(
            "Developer Administrator direct mutation endpoint "
            "is no longer available."
        ),
    )


# ---------------------------------------------------------------------------
# Transaction-authorized Developer Admin mutations
# ---------------------------------------------------------------------------


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
    try:
        authorization = _get_transaction_service(request).create_grant_transaction(
            principal=principal,
            target_user_id=payload.target_user_id,
        )
    except (
        PermissionError,
        TransactionAuthorizationApplicationError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from None

    transaction = authorization.transaction
    risk_context = dict(transaction.risk_context)

    return DeveloperAdminPendingTransactionResponse(
        authorization_id=authorization.authorization_id,
        transaction_id=transaction.transaction_id,
        operation=transaction.operation,
        audience=risk_context["audience"],
        target_user_id=UUID(risk_context["target_user_id"]),
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
    try:
        authorization = _get_transaction_service(request).create_revoke_transaction(
            principal=principal,
            target_user_id=payload.target_user_id,
        )
    except (
        PermissionError,
        TransactionAuthorizationApplicationError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from None

    transaction = authorization.transaction
    risk_context = dict(transaction.risk_context)

    return DeveloperAdminPendingTransactionResponse(
        authorization_id=authorization.authorization_id,
        transaction_id=transaction.transaction_id,
        operation=transaction.operation,
        audience=risk_context["audience"],
        target_user_id=UUID(risk_context["target_user_id"]),
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction authorization was not found.",
        )

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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from None
    except (
        PermissionError,
        TransactionAuthorizationApplicationError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from None

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction authorization was not found.",
        )

    try:
        transaction = authorization.transaction

        if transaction.operation == transaction_service.GRANT_OPERATION:
            await transaction_service.execute_grant(
                principal=principal,
                authorization_id=authorization_id,
                transaction=transaction,
            )
        elif transaction.operation == transaction_service.REVOKE_OPERATION:
            await transaction_service.execute_revoke(
                principal=principal,
                authorization_id=authorization_id,
                transaction=transaction,
            )
        else:
            raise PermissionError(
                "Developer Administrator transaction operation is invalid."
            )

    except DeveloperAdminUserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    except (
        DeveloperAdminUserInactiveError,
        DeveloperAdminLastAdminError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None
    except (
        PermissionError,
        TransactionAuthorizationApplicationError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from None

    consumed = transaction_service.get_authorization(
        authorization_id=authorization_id
    )

    state = (
        consumed.state.value
        if consumed is not None
        else "CONSUMED"
    )

    return DeveloperAdminExecuteTransactionResponse(
        authorization_id=authorization_id,
        state=state,
    )


__all__ = ["router"]