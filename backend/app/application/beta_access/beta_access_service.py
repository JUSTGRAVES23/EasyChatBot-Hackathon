from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from dataclasses import replace

from .models import BetaConnectionToken, BetaUserState, TelegramBinding
from .repositories import (
    BetaTokenRepository,
    BetaUserRepository,
    TelegramBindingRepository,
)

logger = logging.getLogger(__name__)


class BetaAccessService:
    """Application boundary for Beta eligibility and Telegram binding."""

    def __init__(
        self,
        *,
        user_repository: BetaUserRepository,
        token_repository: BetaTokenRepository,
        binding_repository: TelegramBindingRepository,
        expiration_minutes: int = 15,
    ) -> None:
        if expiration_minutes <= 0:
            raise ValueError("expiration_minutes must be positive.")
        self._users = user_repository
        self._tokens = token_repository
        self._bindings = binding_repository
        self._expiration_minutes = expiration_minutes

    async def approve_beta(self, user_id: str) -> BetaUserState:
        user = await self._require_user(user_id)
        if not user.email_verified:
            raise ValueError("Email must be verified before Beta approval.")
        return await self._users.save(replace(user, beta_approved=True))

    async def assign_world(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> BetaUserState:
        if not world_id:
            raise ValueError("world_id is required.")
        user = await self._require_user(user_id)
        if not user.email_verified:
            raise ValueError("Email must be verified before World assignment.")
        if not user.beta_approved:
            raise ValueError("User is not Beta approved.")
        return await self._users.save(
            replace(user, active_world_id=world_id)
        )

    async def create_connection_token(self, user_id: str) -> tuple[str, BetaConnectionToken]:
        user = await self._require_user(user_id)
        if not user.email_verified:
            raise ValueError("Email is not verified.")
        if not user.beta_approved:
            raise ValueError("User is not Beta approved.")
        if not user.active_world_id:
            raise ValueError("User must have a Learning World before Telegram access.")

        raw_token = secrets.token_urlsafe(32)
        token = BetaConnectionToken(
            token_id=secrets.token_hex(16),
            user_id=user.user_id,
            token_hash=self.hash_token(raw_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=self._expiration_minutes),
        )
        await self._tokens.save(token)
        logger.info("Beta Telegram token created user_id=%s", user.user_id)
        return raw_token, token

    async def validate_and_bind(
        self,
        *,
        token: str,
        telegram_id: int,
        chat_id: int,
    ) -> BetaUserState:
        if not token:
            raise ValueError("Connection token is required.")
        if telegram_id <= 0:
            raise ValueError("Telegram ID must be positive.")
        if chat_id == 0:
            raise ValueError("Chat ID is required.")

        record = await self._tokens.get_by_hash(self.hash_token(token))
        if record is None:
            raise ValueError("Invalid connection token.")
        if record.used:
            raise ValueError("Connection token already used.")

        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("Connection token expired.")

        user = await self._require_user(record.user_id)
        if not user.eligible:
            raise ValueError("User is not eligible for Beta Telegram access.")
        if not user.active_world_id:
            raise ValueError("User has no assigned Learning World.")

        existing = await self._users.get_by_telegram_id(telegram_id)
        if existing is not None and existing.user_id != user.user_id:
            raise ValueError("Telegram account is already connected to another user.")

        existing_binding = await self._bindings.get_by_user_id(user.user_id)
        if existing_binding is not None and existing_binding.telegram_user_id != str(telegram_id):
            raise ValueError("User already has another Telegram binding.")

        await self._bindings.save(
            TelegramBinding(
                binding_id=secrets.token_hex(16),
                user_id=user.user_id,
                telegram_user_id=str(telegram_id),
                chat_id=str(chat_id),
                connected_at=datetime.now(timezone.utc),
            )
        )
        await self._tokens.mark_used(
            replace(record, used_at=datetime.now(timezone.utc))
        )
        return await self._users.save(
            replace(user, telegram_id=telegram_id)
        )

    async def authorize_private_chat(self, telegram_id: int) -> BetaUserState:
        if telegram_id <= 0:
            raise ValueError("Telegram ID must be positive.")
        user = await self._users.get_by_telegram_id(telegram_id)
        if user is None:
            raise PermissionError("Telegram account is not connected.")
        if not user.active:
            raise PermissionError(
                "User is connected but is not ACTIVE for a Learning World."
            )
        return user

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def _require_user(self, user_id: str) -> BetaUserState:
        user = await self._users.get(user_id)
        if user is None:
            raise ValueError("Academy user does not exist.")
        return user
