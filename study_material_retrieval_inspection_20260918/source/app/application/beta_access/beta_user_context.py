from dataclasses import dataclass


@dataclass(frozen=True)
class BetaUserContext:

    user_id: str

    telegram_user_id: int

    email: str

    world_id: str

    character: str

    level: str