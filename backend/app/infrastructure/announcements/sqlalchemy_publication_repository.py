"""PostgreSQL adapter for the existing PublicationRepository contract."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.application.announcements.repositories import PublicationRepository
from backend.app.domain.announcements.publication import Publication
from backend.app.domain.announcements.template_models import (
    PublicationStatus,
    PublicationType,
)
from backend.app.infrastructure.persistence.database import Base


class PublicationModel(Base):
    """Canonical durable announcement publication state."""

    __tablename__ = "announcement_publications"

    publication_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    template_id: Mapped[str] = mapped_column(String(255), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    publication_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)


class SqlAlchemyPublicationRepository(PublicationRepository):
    """Async PostgreSQL adapter for the existing repository contract."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    def _to_domain(self, model: PublicationModel) -> Publication:
        return Publication(
            publication_id=model.publication_id,
            template_id=model.template_id,
            template_version=model.template_version,
            publication_type=PublicationType(model.publication_type),
            title=model.title,
            content=model.content,
            status=PublicationStatus(model.status),
            created_at=model.created_at,
            approved_at=model.approved_at,
            published_at=model.published_at,
            failure_reason=model.failure_reason,
        )

    def _from_domain(self, publication: Publication) -> PublicationModel:
        return PublicationModel(
            publication_id=publication.publication_id,
            template_id=publication.template_id,
            template_version=publication.template_version,
            publication_type=publication.publication_type.value,
            title=publication.title,
            content=publication.content,
            status=publication.status.value,
            created_at=publication.created_at or datetime.now(timezone.utc),
            approved_at=publication.approved_at,
            published_at=publication.published_at,
            failure_reason=publication.failure_reason,
        )

    async def save_async(self, publication: Publication) -> None:
        async with self._session_factory() as session:
            model = await session.get(
                PublicationModel,
                publication.publication_id,
            )
            if model is None:
                session.add(self._from_domain(publication))
            else:
                model.template_id = publication.template_id
                model.template_version = publication.template_version
                model.publication_type = publication.publication_type.value
                model.title = publication.title
                model.content = publication.content
                model.status = publication.status.value
                model.created_at = publication.created_at or model.created_at
                model.approved_at = publication.approved_at
                model.published_at = publication.published_at
                model.failure_reason = publication.failure_reason
            await session.commit()

    async def get_async(self, publication_id: str) -> Publication | None:
        async with self._session_factory() as session:
            model = await session.get(PublicationModel, publication_id)
            return self._to_domain(model) if model else None

    async def list_all_async(self) -> tuple[Publication, ...]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PublicationModel).order_by(PublicationModel.created_at)
            )
            return tuple(self._to_domain(model) for model in result.scalars().all())

    # The existing repository contract is synchronous. These methods make
    # accidental async DB use explicit rather than silently blocking.
    def save(self, publication: Publication) -> None:
        raise RuntimeError(
            "SqlAlchemyPublicationRepository requires its async boundary; "
            "use save_async()."
        )

    def get(self, publication_id: str) -> Publication | None:
        raise RuntimeError(
            "SqlAlchemyPublicationRepository requires its async boundary; "
            "use get_async()."
        )

    def list_all(self) -> tuple[Publication, ...]:
        raise RuntimeError(
            "SqlAlchemyPublicationRepository requires its async boundary; "
            "use list_all_async()."
        )
