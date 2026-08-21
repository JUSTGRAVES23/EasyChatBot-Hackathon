from __future__ import annotations

from app.application.beta_access.models import BetaConnectionToken, BetaUserState, TelegramBinding


class InMemoryBetaUserRepository:
    def __init__(self):
        self._users = {}

    async def get(self, user_id):
        return self._users.get(user_id)

    async def save(self, user):
        self._users[user.user_id] = user
        return user

    async def get_by_telegram_id(self, telegram_id):
        return next(
            (u for u in self._users.values() if u.telegram_id == telegram_id),
            None,
        )


class InMemoryBetaTokenRepository:
    def __init__(self):
        self._tokens = {}

    async def save(self, token):
        self._tokens[token.token] = token

    async def get_by_token(self, token):
        return self._tokens.get(token)

    async def mark_used(self, token):
        record = self._tokens[token]
        self._tokens[token] = BetaConnectionToken(
            user_id=record.user_id,
            token=record.token,
            expires_at=record.expires_at,
            used=True,
        )


class InMemoryTelegramBindingRepository:
    def __init__(self):
        self._bindings = {}

    async def save(self, binding):
        self._bindings[binding.telegram_id] = binding
        return binding

    async def get_by_telegram_id(self, telegram_id):
        return self._bindings.get(telegram_id)
