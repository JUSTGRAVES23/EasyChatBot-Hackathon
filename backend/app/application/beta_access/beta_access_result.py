from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BetaAccessStatus(str, Enum):
    CONNECTED = "CONNECTED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_USED = "TOKEN_USED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_NOT_ELIGIBLE = "USER_NOT_ELIGIBLE"
    WORLD_REQUIRED = "WORLD_REQUIRED"
    TELEGRAM_ALREADY_BOUND = "TELEGRAM_ALREADY_BOUND"


@dataclass(frozen=True, slots=True)
class BetaAccessResult:
    status: BetaAccessStatus
    user_id: str | None = None
    world_id: str | None = None
