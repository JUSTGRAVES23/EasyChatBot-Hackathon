from __future__ import annotations

from app.application.authorization.authorization_service import (
    AuthorizationService,
    PermissionDeniedError,
)
from app.domain.authorization.permissions import Permission
from app.domain.identity.principal import Principal


class AuthorizationFunctionalityControlAuthorizer:
    """Application adapter for functionality-control authorization."""

    def __init__(
        self,
        authorization_service: AuthorizationService | None = None,
    ) -> None:
        self._authorization_service = (
            authorization_service or AuthorizationService()
        )

    def can_control_functionality(
        self,
        *,
        actor: object,
        environment: str,
        functionality_id: str,
    ) -> bool:
        if not isinstance(actor, Principal):
            return False

        try:
            self._authorization_service.require_permission(
                principal=actor,
                permission=Permission.FUNCTIONALITY_CONTROL,
            )
        except PermissionDeniedError:
            return False

        return True


__all__ = ["AuthorizationFunctionalityControlAuthorizer"]
