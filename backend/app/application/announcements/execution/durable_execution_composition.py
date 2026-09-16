"""WS-22.3.5.3 canonical durable publication execution composition.

This module is the composition boundary for the WS-22 durable execution
vertical slice.

It deliberately does not create a new persistence architecture. The
canonical PostgreSQL engine and async session factory are supplied by the
platform persistence boundary in:

    app.infrastructure.persistence.database

The resulting object graph is:

    PostgreSQL
        |
        v
    canonical async session factory
        |
        +--> execution repository
        |
        +--> audit repository
                  |
                  v
        DurablePublicationExecutionAudit
                  |
                  v
        DurablePublicationExecutionService

Provider selection remains outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.application.announcements.execution.audit_adapter import (
    DurablePublicationExecutionAudit,
)
from app.application.announcements.execution.durable_execution_service import (
    DurablePublicationExecutionService,
)
from app.infrastructure.announcements.publication_audit_repository import (
    SqlAlchemyPublicationAuditRepository,
)
from app.infrastructure.announcements.sqlalchemy_publication_execution_repository import (
    SqlAlchemyPublicationExecutionRepository,
)
from app.infrastructure.persistence.database import (
    create_async_database_engine,
    create_async_session_factory,
)


@dataclass(frozen=True, slots=True)
class DurablePublicationExecutionComposition:
    """Fully composed WS-22 durable execution boundary."""

    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    execution_repository: SqlAlchemyPublicationExecutionRepository
    audit_repository: SqlAlchemyPublicationAuditRepository
    audit: DurablePublicationExecutionAudit
    service: DurablePublicationExecutionService

    async def dispose(self) -> None:
        """Release the shared PostgreSQL async engine."""

        await self.engine.dispose()


def create_durable_publication_execution_composition(
    *,
    publisher,
) -> DurablePublicationExecutionComposition:
    """Create the canonical WS-22 durable execution graph.

    The publisher is deliberately injected because provider selection belongs
    outside the durable execution composition.

    This function creates exactly one PostgreSQL engine and exactly one async
    session factory. Both durable repositories receive that same factory.
    """

    if publisher is None:
        raise ValueError("publisher cannot be None.")

    engine = create_async_database_engine()
    session_factory = create_async_session_factory(engine)

    execution_repository = SqlAlchemyPublicationExecutionRepository(
        session_factory
    )

    audit_repository = SqlAlchemyPublicationAuditRepository(
        session_factory
    )

    audit = DurablePublicationExecutionAudit(
        repository=audit_repository,
    )

    service = DurablePublicationExecutionService(
        publisher=publisher,
        execution_repository=execution_repository,
        audit=audit,
    )

    return DurablePublicationExecutionComposition(
        engine=engine,
        session_factory=session_factory,
        execution_repository=execution_repository,
        audit_repository=audit_repository,
        audit=audit,
        service=service,
    )


__all__ = [
    "DurablePublicationExecutionComposition",
    "create_durable_publication_execution_composition",
]
