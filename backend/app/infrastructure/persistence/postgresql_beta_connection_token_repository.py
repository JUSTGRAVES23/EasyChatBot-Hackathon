from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.beta_access.beta_access_repository import BetaConnectionTokenRepository
from app.domain.beta_access.beta_connection_token import BetaConnectionToken
from app.infrastructure.persistence.beta_connection_token_models import BetaConnectionTokenModel


class PostgreSQLBetaConnectionTokenRepository(BetaConnectionTokenRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, token: BetaConnectionToken) -> None:
        self._session.add(BetaConnectionTokenModel(
            id=token.id, user_id=token.user_id, token_hash=token.token_hash,
            expires_at=token.expires_at, used_at=token.used_at, created_at=token.created_at,
        ))
        self._session.flush()

    def get_by_hash(self, token_hash: str) -> BetaConnectionToken | None:
        row = self._session.scalar(select(BetaConnectionTokenModel).where(
            BetaConnectionTokenModel.token_hash == token_hash
        ))
        if row is None:
            return None
        return BetaConnectionToken(
            id=row.id, user_id=row.user_id, token_hash=row.token_hash,
            expires_at=row.expires_at, created_at=row.created_at, used_at=row.used_at,
        )

    def mark_used(self, token_id: str, used_at: datetime) -> None:
        self._session.execute(
            update(BetaConnectionTokenModel)
            .where(BetaConnectionTokenModel.id == token_id)
            .where(BetaConnectionTokenModel.used_at.is_(None))
            .values(used_at=used_at)
        )
        self._session.flush()

