from __future__ import annotations

from app.domain.authorization.permissions import Permission, has_permission
from app.domain.identity.principal import Principal


class AuthenticationRequiredError(PermissionError):
    """No valid authenticated principal exists."""


class PermissionDeniedError(PermissionError):
    """Authenticated principal lacks a permission."""


class AuthorizationService:
    """Provider-neutral authorization boundary."""

    def require_authenticated(
        self,
        principal: Principal | None,
    ) -> Principal:
        if principal is None or not principal.is_active:
            raise AuthenticationRequiredError(
                "Authenticated application identity is required."
            )
        return principal

    def require_permission(
        self,
        *,
        principal: Principal | None,
        permission: Permission,
    ) -> Principal:
        authenticated = self.require_authenticated(principal)

        if not has_permission(
            roles=authenticated.roles,
            permission=permission,
        ):
            raise PermissionDeniedError(
                f"Permission required: {permission.value}."
            )

        return authenticated




