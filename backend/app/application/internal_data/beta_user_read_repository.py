from __future__ import annotations

from typing import Protocol

# IMPORTANT:
# Replace this import with the actual BetaUserState module path
# discovered in step 2 if the repository uses a different location.
from app.application.beta_access.models import BetaUserState


class BetaUserReadRepository(Protocol):
    """Read-only application port for Beta-user data.

    This interface intentionally exposes no write operation.
    """

    async def get(
        self,
        user_id: str,
    ) -> BetaUserState | None:
        """Return a Beta user by internal user ID."""
        ...

    async def get_by_telegram_id(
        self,
        telegram_id: int,
    ) -> BetaUserState | None:
        """Return a Beta user by Telegram ID."""
        ...

