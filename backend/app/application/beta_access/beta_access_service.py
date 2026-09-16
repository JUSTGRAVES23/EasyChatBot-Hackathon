from __future__ import annotations

import hashlib
import logging
import secrets

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Iterator

from app.application.uai.world.world_resolver import WorldResolver

from .models import (
    BetaConnectionToken,
    BetaUserState,
    TelegramBinding,
)

from .repositories import (
    BetaTokenRepository,
    BetaUserRepository,
    TelegramBindingRepository,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BetaConnectionTokenResult:
    token: str
    connection: BetaConnectionToken

    def __iter__(self) -> Iterator[object]:
        yield self.token
        yield self.connection


@dataclass(frozen=True)
class BetaConversationContext:
    user_id: str
    telegram_user_id: int
    email: str
    world_id: str
    language_code: str | None
    character: str
    level: str


class BetaAccessService:
    """
    Application boundary for Beta eligibility,
    Telegram binding and authorization.

    Telegram identity invariant:

        One Telegram identity
        -> one Beta account

    A Telegram identity that is already connected cannot
    be rebound to another Beta account through a new
    connection token.

    World assignment invariant:

        A world must be resolved through the authoritative
        WorldResolver before its ID can be persisted as the
        user's active world.

    World conversation invariant:

        A conversation context must be derived from the
        user's persisted active World through WorldResolver.

        Missing or invalid World configuration fails closed.
        The service never silently substitutes a default World.

    World compatibility:

        Legacy Beta/Telegram world identifier:
            world-fr

        Canonical World identifier:
            french_world

    Legacy identifiers are accepted only at this application
    compatibility boundary. New persisted assignments always
    use the canonical identifier returned by WorldResolver.
    """

    LEGACY_WORLD_ALIASES = {
        "world-fr": "french_world",
    }

    def __init__(
        self,
        *,
        user_repository: BetaUserRepository,
        token_repository: BetaTokenRepository,
        binding_repository: TelegramBindingRepository,
        world_resolver: WorldResolver,
        expiration_minutes: int = 1440,
    ) -> None:
        if expiration_minutes <= 0:
            raise ValueError(
                "expiration_minutes must be positive."
            )

        self._users = user_repository
        self._tokens = token_repository
        self._bindings = binding_repository
        self._world_resolver = world_resolver
        self._expiration_minutes = expiration_minutes

    async def approve_beta(
        self,
        user_id: str,
    ) -> BetaUserState:
        user = await self._require_user(user_id)

        if not user.email_verified:
            raise ValueError(
                "Email must be verified before Beta approval."
            )

        return await self._users.save(
            replace(
                user,
                beta_approved=True,
            )
        )

    async def assign_world(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> BetaUserState:
        if not world_id:
            raise ValueError(
                "world_id is required."
            )

        user = await self._require_user(user_id)

        if not user.email_verified:
            raise ValueError(
                "Email must be verified before World assignment."
            )

        if not user.beta_approved:
            raise ValueError(
                "User is not Beta approved."
            )

        # Resolve legacy application identifiers to the canonical
        # World identifier before crossing the authoritative
        # WorldResolver boundary.
        canonical_world_id = self.LEGACY_WORLD_ALIASES.get(
            world_id,
            world_id,
        )

        # Resolve the requested World before persistence.
        #
        # This is the authoritative World catalogue boundary.
        # If the World does not exist or is invalid, WorldResolver
        # raises and active_world_id is not modified.
        world = self._world_resolver.resolve(
            canonical_world_id,
        )

        return await self._users.save(
            replace(
                user,
                active_world_id=world.world_id,
            )
        )

    async def create_connection_token(
        self,
        user_id: str,
    ) -> BetaConnectionTokenResult:
        user = await self._require_user(user_id)

        if not user.email_verified:
            raise ValueError(
                "Email is not verified."
            )

        if not user.beta_approved:
            raise ValueError(
                "User is not Beta approved."
            )

        if not user.active_world_id:
            raise ValueError(
                "User must have a Learning World before Telegram access."
            )

        raw_token = secrets.token_urlsafe(32)

        token = BetaConnectionToken(
            token_id=secrets.token_hex(16),
            user_id=user.user_id,
            token_hash=self.hash_token(
                raw_token
            ),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(
                    minutes=self._expiration_minutes
                )
            ),
        )

        await self._tokens.save(token)

        return BetaConnectionTokenResult(
            token=raw_token,
            connection=token,
        )

    async def validate_and_bind(
        self,
        *,
        token: str,
        telegram_id: int,
        chat_id: int,
    ) -> BetaUserState:
        record = await self._tokens.get_by_hash(
            self.hash_token(token)
        )

        if record is None:
            raise ValueError(
                "Invalid connection token."
            )

        if record.used:
            raise ValueError(
                "Connection token already used."
            )

        expires_at = record.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if expires_at <= datetime.now(timezone.utc):
            raise ValueError(
                "Connection token expired."
            )

        user = await self._require_user(
            record.user_id
        )

        if not user.eligible:
            raise ValueError(
                "User is not eligible."
            )

        # -------------------------------------------------
        # Telegram identity ownership invariant
        #
        # A Telegram identity may belong to only one
        # Beta account. Never silently transfer ownership.
        # -------------------------------------------------

        existing_binding = (
            await self._bindings.get_by_telegram_user_id(
                str(telegram_id)
            )
        )

        if existing_binding is not None:
            raise ValueError(
                "Telegram identity is already connected."
            )

        await self._bindings.save(
            TelegramBinding(
                binding_id=secrets.token_hex(16),
                user_id=user.user_id,
                telegram_user_id=str(
                    telegram_id
                ),
                chat_id=str(
                    chat_id
                ),
                connected_at=datetime.now(
                    timezone.utc
                ),
            )
        )

        await self._tokens.mark_used(
            replace(
                record,
                used_at=datetime.now(
                    timezone.utc
                ),
            )
        )

        return await self._users.save(
            replace(
                user,
                telegram_id=telegram_id,
            )
        )

    async def authorize_private_chat(
        self,
        telegram_id: int,
    ) -> BetaUserState:
        user = await self._users.get_by_telegram_id(
            telegram_id
        )

        if user is None:
            raise PermissionError(
                "Telegram account is not connected."
            )

        if not user.active:
            raise PermissionError(
                "User is not active."
            )

        return user

    async def get_conversation_context(
        self,
        telegram_user_id: int,
    ) -> BetaConversationContext:
        """
        Resolve the authoritative conversation context for
        an authorized Telegram learner.

        The persisted active_world_id is treated only as the
        World identifier. The authoritative World configuration,
        including its language code, is always obtained through
        WorldResolver.

        This method deliberately fails closed when no active World
        is assigned or when the assigned World cannot be resolved.
        """

        user = await self.authorize_private_chat(
            telegram_user_id
        )

        if not user.active_world_id:
            raise ValueError(
                "Active learning World is required."
            )

        canonical_world_id = self._canonical_world_id(
            user.active_world_id
        )

        # WorldResolver is the authoritative runtime World boundary.
        # No language or World defaults are inferred here.
        world = self._world_resolver.resolve(
            canonical_world_id
        )

        return BetaConversationContext(
            user_id=user.user_id,
            telegram_user_id=telegram_user_id,
            email=user.email,
            world_id=world.world_id,
            language_code=world.language_code,
            character="Alix",
            level="B1",
        )

    @classmethod
    def _canonical_world_id(
        cls,
        world_id: str | None,
    ) -> str:
        """
        Convert an accepted legacy application identifier to the
        canonical World identifier.

        A missing identifier is intentionally not replaced with a
        default World. Callers must fail closed instead.
        """

        if not world_id:
            raise ValueError(
                "Active learning World is required."
            )

        return cls.LEGACY_WORLD_ALIASES.get(
            world_id,
            world_id,
        )

    @staticmethod
    def hash_token(
        token: str,
    ) -> str:
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    async def _require_user(
        self,
        user_id: str,
    ) -> BetaUserState:
        user = await self._users.get(
            user_id
        )

        if user is None:
            raise ValueError(
                "Academy user does not exist."
            )

        return user


__all__ = [
    "BetaAccessService",
    "BetaConnectionTokenResult",
    "BetaConversationContext",
]