from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class PublicationAuditEventModel(Base):
    """Immutable persisted publication audit event."""

    __tablename__ = "announcement_publication_audit_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    publication_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    correlation_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    provider_message_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    error_code: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class SqlAlchemyPublicationAuditRepository:
    """Persist publication execution audit using the existing session factory."""

    def __init__(self, session_factory) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    async def record_success(
        self,
        *,
        publication_id: UUID,
        actor: str,
        correlation_id: str,
        provider_message_id: str | None,
    ) -> None:
        await self._record(
            publication_id=publication_id,
            event_type="published",
            actor=actor,
            correlation_id=correlation_id,
            provider_message_id=provider_message_id,
            error_code=None,
            details=None,
        )

    async def record_failure(
        self,
        *,
        publication_id: UUID,
        actor: str,
        correlation_id: str,
        error_code: str,
    ) -> None:
        await self._record(
            publication_id=publication_id,
            event_type="publish_failed",
            actor=actor,
            correlation_id=correlation_id,
            provider_message_id=None,
            error_code=error_code,
            details=None,
        )

    async def list_for(
        self, publication_id: UUID
    ) -> tuple[PublicationAuditEventModel, ...]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PublicationAuditEventModel)
                .where(
                    PublicationAuditEventModel.publication_id
                    == str(publication_id)
                )
                .order_by(PublicationAuditEventModel.id)
            )
            return tuple(result.scalars().all())

    async def _record(
        self,
        *,
        publication_id: UUID,
        event_type: str,
        actor: str,
        correlation_id: str,
        provider_message_id: str | None,
        error_code: str | None,
        details: str | None,
    ) -> None:
        event = PublicationAuditEventModel(
            publication_id=str(publication_id),
            event_type=event_type,
            actor=actor,
            correlation_id=correlation_id,
            provider_message_id=provider_message_id,
            error_code=error_code,
            details=details,
            occurred_at=datetime.now(timezone.utc),
        )
        async with self._session_factory() as session:
            session.add(event)
            await session.commit()

