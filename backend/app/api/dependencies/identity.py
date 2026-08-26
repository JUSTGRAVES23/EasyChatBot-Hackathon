from __future__ import annotations

from fastapi import HTTPException, Request, status

from backend.app.domain.identity.principal import Principal
from backend.app.infrastructure.auth.session_identity_provider import (
    SessionIdentityProvider,
)


async def get_current_principal(request: Request) -> Principal:
    """Resolve identity from the HttpOnly application session cookie."""

    session_id = request.cookies.get("easychatbot_session")

    repository = request.app.state.auth_repository

    provider = SessionIdentityProvider(
        session_id=session_id,
        repository=repository,
    )

    principal = await provider.get_current_principal()

    if principal is None or not principal.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    return principal
