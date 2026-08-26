from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AccountStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated application identity."""

    user_id: str
    email: str
    email_verified: bool
    account_status: AccountStatus
    roles: frozenset[str] = frozenset()

    @property
    def is_active(self) -> bool:
        return (
            self.account_status == AccountStatus.ACTIVE
            and self.email_verified
        )
