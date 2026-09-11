from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.api.dependencies.identity import get_current_principal
from app.application.authorization.authorization_service import (
    AuthorizationService,
    PermissionDeniedError,
)
from app.domain.authorization.permissions import Permission
from app.domain.identity.principal import Principal


def require_permission(permission: Permission):
    async def dependency(
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        try:
            return AuthorizationService().require_permission(
                principal=principal,
                permission=permission,
            )
        except PermissionDeniedError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission.",
            ) from None

    return dependency
