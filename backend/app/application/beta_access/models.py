from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class BetaAccessStatus(StrEnum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ELIGIBLE = "ELIGIBLE"
    TELEGRAM_CONNECTED = "TELEGRAM_CONNECTED"
    ACTIVE = "ACTIVE"
    DENIED = "DENIED"


@dataclass(frozen=True, slots=True)
class BetaUserState:
    user_id: str
    email: str
    email_verified: bool
    beta_approved: bool
    telegram_id: int | None = None
    active_world_id: str | None = None

    @property
    def eligible(self) -> bool:
        return self.email_verified and self.beta_approved

    @property
    def active(self) -> bool:
        return (
            self.eligible
            and self.telegram_id is not None
            and self.active_world_id is not None
        )


@dataclass(frozen=True, slots=True)
class BetaConnectionToken:
    token_id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None

    @property
    def used(self) -> bool:
        return self.used_at is not None


@dataclass(frozen=True, slots=True)
class TelegramBinding:
    binding_id: str
    user_id: str
    telegram_user_id: str
    chat_id: str
    connected_at: datetime
