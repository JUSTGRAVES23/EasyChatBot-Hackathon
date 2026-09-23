from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.telegram_update_idempotency import (
    TelegramUpdateIdempotencyPort,
)
from app.infrastructure.persistence.telegram_update_idempotency_models import (
    TelegramUpdateIdempotencyRecord,
)


class PostgreSQLTelegramUpdateIdempotencyRepository(
    TelegramUpdateIdempotencyPort
):
    """
    PostgreSQL implementation of the Telegram inbound update claim.

    The claim is performed using PostgreSQL's atomic
    INSERT ... ON CONFLICT DO NOTHING semantics.

    This avoids an application-level check-then-insert race when multiple
    application instances receive the same Telegram update concurrently.
    """

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def claim(self, telegram_update_id: int) -> bool:
        if telegram_update_id < 0:
            raise ValueError("telegram_update_id must be non-negative.")

        statement = (
            insert(TelegramUpdateIdempotencyRecord)
            .values(
                telegram_update_id=telegram_update_id,
                status="CLAIMED",
            )
            .on_conflict_do_nothing(
                index_elements=[
                    TelegramUpdateIdempotencyRecord.telegram_update_id
                ]
            )
        )

        with self._session_factory() as session:
            result = session.execute(statement)
            session.commit()
            return result.rowcount == 1


__all__ = ["PostgreSQLTelegramUpdateIdempotencyRepository"]
