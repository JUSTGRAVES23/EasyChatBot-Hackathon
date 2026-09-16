from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.developer_admin.developer_admin_audit import DeveloperAdminAuditEvent
from app.infrastructure.auth.postgresql_auth_repository import AuthUserRecord
from app.infrastructure.developer_admin.postgresql_developer_admin_audit_repository import (
    PostgreSQLDeveloperAdminAuditRepository,
)


class PostgreSQLDeveloperAdminUnitOfWork:
    """Single PostgreSQL transaction for Developer Admin role + audit changes.

    A PostgreSQL transaction-scoped advisory lock serializes Developer Admin
    mutations so the last-admin invariant cannot race with another mutation.
    """

    _MUTATION_LOCK_KEY = 84172931

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        audit_repository: PostgreSQLDeveloperAdminAuditRepository | None = None,
    ) -> None:
        if session_factory is None:
            raise ValueError("session_factory is required.")
        self._session_factory = session_factory
        self._audit_repository = audit_repository
        self._session: AsyncSession | None = None
        self._transaction = None

    async def __aenter__(self) -> "PostgreSQLDeveloperAdminUnitOfWork":
        self._session = self._session_factory()
        self._transaction = await self._session.begin()
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": self._MUTATION_LOCK_KEY},
        )
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        try:
            if self._transaction is not None and self._transaction.is_active:
                if exc_type is None:
                    await self._transaction.commit()
                else:
                    await self._transaction.rollback()
        finally:
            if self._session is not None:
                await self._session.close()
            self._session = None
            self._transaction = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("Developer Admin unit of work is not active.")
        return self._session

    async def get_user(self, user_id: UUID) -> AuthUserRecord | None:
        result = await self.session.execute(
            text(
                """
                SELECT id, email, username, status, email_verified
                FROM users
                WHERE id = :user_id
                LIMIT 1
                FOR UPDATE
                """
            ),
            {"user_id": user_id},
        )
        row = result.mappings().first()
        if row is None:
            return None
        return AuthUserRecord(
            id=row["id"],
            email=row["email"],
            username=row["username"],
            status=row["status"],
            email_verified=bool(row["email_verified"]),
        )

    async def get_user_roles(self, user_id: UUID) -> tuple[str, ...]:
        result = await self.session.execute(
            text(
                """
                SELECT role
                FROM auth_user_roles
                WHERE user_id = :user_id
                ORDER BY role
                """
            ),
            {"user_id": user_id},
        )
        return tuple(row[0] for row in result.all())

    async def count_users_with_role(self, role: str) -> int:
        result = await self.session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM auth_user_roles
                WHERE role = :role
                """
            ),
            {"role": role},
        )
        return int(result.scalar_one())

    async def add_user_role(self, *, user_id: UUID, role: str) -> bool:
        result = await self.session.execute(
            text(
                """
                INSERT INTO auth_user_roles (user_id, role)
                VALUES (:user_id, :role)
                ON CONFLICT DO NOTHING
                """
            ),
            {"user_id": user_id, "role": role},
        )
        return result.rowcount == 1

    async def remove_user_role(self, *, user_id: UUID, role: str) -> bool:
        result = await self.session.execute(
            text(
                """
                DELETE FROM auth_user_roles
                WHERE user_id = :user_id
                  AND role = :role
                """
            ),
            {"user_id": user_id, "role": role},
        )
        return result.rowcount == 1

    async def record_audit(self, event: DeveloperAdminAuditEvent) -> DeveloperAdminAuditEvent:
        if self._audit_repository is None:
            raise RuntimeError("Developer Admin audit repository is required.")
        return await self._audit_repository.record_in_session(self.session, event)
