from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.beta_access.beta_connection_token import BetaConnectionToken


class BetaConnectionTokenRepository(Protocol):
    def add(self, token: BetaConnectionToken) -> None: ...
    def get_by_hash(self, token_hash: str) -> BetaConnectionToken | None: ...
    def mark_used(self, token_id: str, used_at: datetime) -> None: ...

