"""SQLAlchemy durable execution repository for WS-22.

Uses the canonical EasyChatBot SQLAlchemy Base. This module deliberately does
not create a second DeclarativeBase/metadata registry.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.application.announcements.execution.durable_contracts import (
    DurableExecutionStatus,
    PublicationExecutionRecord,
    PublicationExecutionRepository,
)
from app.infrastructure.persistence.database import Base


class PublicationExecutionRecordModel(Base):
    """Durable operational state for a WS-22 publication execution."""

    __tablename__ = "announcement_publication_executions"

    publication_id: Mapped[str] = mapped_column(String(36), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(255), primary_key=True
    )
    correlation_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    attempt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    provider_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class SqlAlchemyPublicationExecutionRepository(
    PublicationExecutionRepository
):
    """Durable repository using the existing injected async session factory."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")

        self._session_factory = session_factory

    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> PublicationExecutionRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PublicationExecutionRecordModel).where(
                    PublicationExecutionRecordModel.idempotency_key
                    == idempotency_key
                )
            )
            model = result.scalar_one_or_none()

            return self._to_domain(model) if model else None

    async def create_started(
        self,
        *,
        publication_id,
        idempotency_key,
        correlation_id,
    ) -> PublicationExecutionRecord:
        """Create the first durable execution attempt."""

        now = datetime.now(timezone.utc)

        model = PublicationExecutionRecordModel(
            publication_id=str(publication_id),
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            attempt=1,
            status=DurableExecutionStatus.STARTED.value,
            created_at=now,
            updated_at=now,
        )

        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
            await session.refresh(model)

            return self._to_domain(model)

    async def mark_succeeded(
        self,
        *,
        idempotency_key,
        provider_message_id,
    ) -> PublicationExecutionRecord:
        """Persist successful completion without changing the attempt count."""

        return await self._update(
            idempotency_key,
            status=DurableExecutionStatus.SUCCEEDED.value,
            provider_message_id=provider_message_id,
            error_code=None,
        )

    async def mark_failed(
        self,
        *,
        idempotency_key,
        error_code,
    ) -> PublicationExecutionRecord:
        """Persist failure while retaining the current attempt number."""

        return await self._update(
            idempotency_key,
            status=DurableExecutionStatus.FAILED.value,
            error_code=error_code,
        )

    async def start_retry(
        self,
        *,
        idempotency_key: str,
    ) -> PublicationExecutionRecord:
        """Increment the durable attempt counter for a retry.

        A retry is valid only for an existing FAILED execution. The same
        idempotency record is retained; no second database row is created.
        """

        async with self._session_factory() as session:
            result = await session.execute(
                select(PublicationExecutionRecordModel).where(
                    PublicationExecutionRecordModel.idempotency_key
                    == idempotency_key
                )
            )

            model = result.scalar_one()

            if model.status != DurableExecutionStatus.FAILED.value:
                raise ValueError(
                    "Only failed executions can be retried."
                )

            model.attempt += 1
            model.status = DurableExecutionStatus.STARTED.value
            model.error_code = None
            model.provider_message_id = None
            model.updated_at = datetime.now(timezone.utc)

            await session.commit()
            await session.refresh(model)

            return self._to_domain(model)

    async def _update(
        self,
        idempotency_key,
        **values,
    ) -> PublicationExecutionRecord:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PublicationExecutionRecordModel).where(
                    PublicationExecutionRecordModel.idempotency_key
                    == idempotency_key
                )
            )

            model = result.scalar_one()

            for key, value in values.items():
                setattr(model, key, value)

            model.updated_at = datetime.now(timezone.utc)

            await session.commit()
            await session.refresh(model)

            return self._to_domain(model)

    @staticmethod
    def _to_domain(
        model: PublicationExecutionRecordModel,
    ) -> PublicationExecutionRecord:
        return PublicationExecutionRecord(
            publication_id=UUID(model.publication_id),
            idempotency_key=model.idempotency_key,
            correlation_id=model.correlation_id,
            attempt=model.attempt,
            status=DurableExecutionStatus(model.status),
            provider_message_id=model.provider_message_id,
            error_code=model.error_code,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
