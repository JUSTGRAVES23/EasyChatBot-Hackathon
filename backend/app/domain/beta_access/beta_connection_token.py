from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BetaConnectionToken:
    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    created_at: datetime
    used_at: datetime | None = None

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at
