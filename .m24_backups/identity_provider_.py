from __future__ import annotations

from typing import Protocol

from app.domain.identity.principal import Principal


class IdentityProvider(Protocol):
    """Provider-neutral identity contract."""

    async def get_current_principal(self) -> Principal | None:
        ...