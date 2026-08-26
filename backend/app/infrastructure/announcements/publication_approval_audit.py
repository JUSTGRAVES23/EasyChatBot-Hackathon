from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.domain.announcements.publication import Publication
from backend.app.infrastructure.persistence.database import Base


class PublicationApprovalAuditEventModel(Base):
    """Durable audit evidence for human approval decisions."""

    __tablename__ = "announcement_publication_approval_audit_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    publication_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    details: Mapped[str | None] = mapped_column(Text, nullable=True)


class SqlAlchemyPublicationApprovalAudit:
    """Persist approval evidence using the canonical async session factory."""

    def __init__(self, session_factory) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    async def record_approval(
        self,
        *,
        publication: Publication,
        actor: str,
        occurred_at: datetime,
    ) -> None:
        if not actor.strip():
            raise ValueError("actor cannot be empty.")

        event = PublicationApprovalAuditEventModel(
            publication_id=publication.publication_id,
            event_type="approved",
            actor=actor.strip(),
            occurred_at=occurred_at,
            details="Publication transitioned to APPROVED.",
        )

        async with self._session_factory() as session:
            session.add(event)
            await session.commit()

    async def list_for(
        self,
        publication_id: str,
    ) -> tuple[PublicationApprovalAuditEventModel, ...]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PublicationApprovalAuditEventModel)
                .where(
                    PublicationApprovalAuditEventModel.publication_id
                    == publication_id
                )
                .order_by(PublicationApprovalAuditEventModel.id)
            )
            return tuple(result.scalars().all())


__all__ = [
    "PublicationApprovalAuditEventModel",
    "SqlAlchemyPublicationApprovalAudit",
]
