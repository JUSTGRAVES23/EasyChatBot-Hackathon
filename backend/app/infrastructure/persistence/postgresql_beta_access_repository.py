from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select

from app.application.beta_access.models import (
    BetaConnectionToken,
    BetaUserState,
    TelegramBinding,
)
from app.application.beta_access.repositories import (
    BetaTokenRepository,
    BetaUserRepository,
    TelegramBindingRepository,
)
from .beta_access_models import (
    BetaConnectionTokenRecord,
    BetaUserRecord,
    TelegramBindingRecord,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PostgreSQLBetaUserRepository(BetaUserRepository):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get(self, user_id: str) -> BetaUserState | None:
        with self._session_factory() as session:
            row = session.get(BetaUserRecord, user_id)
            return None if row is None else _user_from_record(row)

    async def get_by_telegram_id(self, telegram_id: int) -> BetaUserState | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(BetaUserRecord).where(
                    BetaUserRecord.telegram_id == str(telegram_id)
                )
            )
            return None if row is None else _user_from_record(row)

    async def save(self, user: BetaUserState) -> BetaUserState:
        now = _utcnow()
        with self._session_factory() as session:
            row = session.get(BetaUserRecord, user.user_id)
            if row is None:
                row = BetaUserRecord(
                    id=user.user_id,
                    email=user.email,
                    email_verified=user.email_verified,
                    approved=user.beta_approved,
                    active_world_id=user.active_world_id,
                    telegram_id=None if user.telegram_id is None else str(user.telegram_id),
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
            else:
                row.email = user.email
                row.email_verified = user.email_verified
                row.approved = user.beta_approved
                row.active_world_id = user.active_world_id
                row.telegram_id = None if user.telegram_id is None else str(user.telegram_id)
                row.updated_at = now
            session.commit()
        return user


class PostgreSQLBetaTokenRepository(BetaTokenRepository):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_by_hash(self, token_hash: str) -> BetaConnectionToken | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(BetaConnectionTokenRecord).where(
                    BetaConnectionTokenRecord.token_hash == token_hash
                )
            )
            return None if row is None else _token_from_record(row)

    async def save(self, token: BetaConnectionToken) -> BetaConnectionToken:
        now = _utcnow()
        with self._session_factory() as session:
            row = session.get(BetaConnectionTokenRecord, token.token_id)
            if row is None:
                session.add(
                    BetaConnectionTokenRecord(
                        id=token.token_id,
                        token_hash=token.token_hash,
                        user_id=token.user_id,
                        expires_at=token.expires_at,
                        used_at=token.used_at,
                        created_at=now,
                    )
                )
            else:
                row.used_at = token.used_at
            session.commit()
        return token

    async def mark_used(self, token: BetaConnectionToken) -> BetaConnectionToken:
        return await self.save(token)


class PostgreSQLTelegramBindingRepository(TelegramBindingRepository):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_by_telegram_user_id(self, telegram_user_id: str) -> TelegramBinding | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(TelegramBindingRecord).where(
                    TelegramBindingRecord.telegram_user_id == telegram_user_id
                )
            )
            return None if row is None else _binding_from_record(row)

    async def get_by_user_id(self, user_id: str) -> TelegramBinding | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(TelegramBindingRecord).where(
                    TelegramBindingRecord.user_id == user_id
                )
            )
            return None if row is None else _binding_from_record(row)

    async def save(self, binding: TelegramBinding) -> TelegramBinding:
        with self._session_factory() as session:
            row = session.get(TelegramBindingRecord, binding.binding_id)
            if row is None:
                session.add(
                    TelegramBindingRecord(
                        id=binding.binding_id,
                        user_id=binding.user_id,
                        telegram_user_id=binding.telegram_user_id,
                        chat_id=binding.chat_id,
                        connected_at=binding.connected_at,
                    )
                )
            else:
                row.telegram_user_id = binding.telegram_user_id
                row.chat_id = binding.chat_id
                row.connected_at = binding.connected_at
            session.commit()
        return binding


def _user_from_record(row: BetaUserRecord) -> BetaUserState:
    return BetaUserState(
        user_id=row.id,
        email=row.email,
        email_verified=row.email_verified,
        beta_approved=row.approved,
        telegram_id=None if row.telegram_id is None else int(row.telegram_id),
        active_world_id=row.active_world_id,
    )


def _token_from_record(row: BetaConnectionTokenRecord) -> BetaConnectionToken:
    return BetaConnectionToken(
        token_id=row.id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        used_at=row.used_at,
    )


def _binding_from_record(row: TelegramBindingRecord) -> TelegramBinding:
    return TelegramBinding(
        binding_id=row.id,
        user_id=row.user_id,
        telegram_user_id=row.telegram_user_id,
        chat_id=row.chat_id,
        connected_at=row.connected_at,
    )
