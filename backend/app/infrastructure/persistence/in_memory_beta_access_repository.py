from __future__ import annotations

from typing import Optional

from app.application.beta_access.models import (
    BetaConnectionToken,
    BetaUserState,
    TelegramBinding,
)


class InMemoryBetaUserRepository:
    def __init__(self) -> None:
        self._users: dict[str, BetaUserState] = {}

    async def save(self, user: BetaUserState) -> BetaUserState:
        self._users[user.user_id] = user
        return user

    async def get(
        self,
        user_id: str,
    ) -> Optional[BetaUserState]:
        return self._users.get(user_id)

    async def get_by_telegram_id(
        self,
        telegram_id: int,
    ) -> Optional[BetaUserState]:
        for user in self._users.values():
            if getattr(user, "telegram_id", None) == telegram_id:
                return user

        return None


class InMemoryBetaTokenRepository:
    def __init__(self) -> None:
        self._tokens: dict[str, BetaConnectionToken] = {}

    async def save(
        self,
        token: BetaConnectionToken,
    ) -> BetaConnectionToken:
        self._tokens[token.token_id] = token
        return token

    async def get(
        self,
        token_id: str,
    ) -> Optional[BetaConnectionToken]:
        return self._tokens.get(token_id)

    async def get_by_hash(
        self,
        token_hash: str,
    ) -> Optional[BetaConnectionToken]:
        for token in self._tokens.values():
            if token.token_hash == token_hash:
                return token

        return None

    async def mark_used(
        self,
        token: BetaConnectionToken,
    ) -> BetaConnectionToken:
        """
        Persist the token with its used_at timestamp.

        The application service passes an immutable replacement of
        the existing token, so the in-memory repository simply replaces
        the stored record.
        """
        self._tokens[token.token_id] = token
        return token


class InMemoryTelegramBindingRepository:
    def __init__(self) -> None:
        self._bindings: dict[str, TelegramBinding] = {}

    async def save(
        self,
        binding: TelegramBinding,
    ) -> TelegramBinding:
        self._bindings[binding.telegram_user_id] = binding
        return binding

    async def get_by_telegram_user_id(
        self,
        telegram_user_id: str,
    ) -> Optional[TelegramBinding]:
        return self._bindings.get(telegram_user_id)

    async def get_by_user_id(
        self,
        user_id: str,
    ) -> Optional[TelegramBinding]:
        for binding in self._bindings.values():
            if binding.user_id == user_id:
                return binding

        return None