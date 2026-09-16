from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.developer_admin.developer_admin_uow_factory import (
    DeveloperAdminUnitOfWorkFactory,
)
from app.infrastructure.developer_admin.postgresql_developer_admin_audit_repository import (
    PostgreSQLDeveloperAdminAuditRepository,
)
from app.infrastructure.developer_admin.postgresql_developer_admin_uow import (
    PostgreSQLDeveloperAdminUnitOfWork,
)


class PostgreSQLDeveloperAdminUnitOfWorkFactory(
    DeveloperAdminUnitOfWorkFactory,
):
    """Creates a fresh PostgreSQL Developer Admin UoW per operation."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        if session_factory is None:
            raise ValueError("session_factory is required.")

        self._session_factory = session_factory

    def create(self) -> PostgreSQLDeveloperAdminUnitOfWork:
        """Create a new UoW with no shared transaction/session state."""

        audit_repository = PostgreSQLDeveloperAdminAuditRepository(
            self._session_factory,
        )

        return PostgreSQLDeveloperAdminUnitOfWork(
            self._session_factory,
            audit_repository=audit_repository,
        )