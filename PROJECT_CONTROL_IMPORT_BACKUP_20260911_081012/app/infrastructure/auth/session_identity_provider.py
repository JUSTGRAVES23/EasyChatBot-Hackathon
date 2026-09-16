from __future__ import annotations

from datetime import datetime, timezone

from app.application.identity.identity_provider import IdentityProvider
from app.domain.identity.principal import AccountStatus, Principal


class SessionIdentityProvider(IdentityProvider):
    """Resolve the authenticated Principal from a server-side session."""

    def __init__(
        self,
        *,
        session_id: str | None,
        repository,
    ) -> None:
        self._session_id = session_id
        self._repository = repository

    async def get_current_principal(self) -> Principal | None:
        if not self._session_id:
            return None

        session = await self._repository.get_session(self._session_id)

        if session is None:
            return None

        now = datetime.now(timezone.utc)

        if session.is_revoked or session.expires_at <= now:
            return None

        user = await self._repository.get_user_for_identity(
            session.user_id
        )

        if user is None:
            return None

        roles = await self._repository.get_user_roles(user.id)

        try:
            status = AccountStatus(user.status)
        except ValueError:
            return None

        return Principal(
            user_id=str(user.id),
            email=user.email,
            email_verified=bool(user.email_verified),
            account_status=status,
            roles=frozenset(roles),
        )



