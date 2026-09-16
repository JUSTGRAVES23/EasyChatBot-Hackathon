from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.application.developer_admin.developer_admin_audit import (
    DeveloperAdminAuditEvent,
)


class DeveloperAdminUnitOfWork(Protocol):
    """Application contract for one atomic Developer Admin transaction."""

    async def __aenter__(self) -> "DeveloperAdminUnitOfWork": ...

    async def __aexit__(self, exc_type, exc, traceback) -> None: ...

    async def get_user(self, user_id: UUID): ...

    async def get_user_roles(self, user_id: UUID) -> tuple[str, ...]: ...

    async def count_users_with_role(self, role: str) -> int: ...

    async def add_user_role(self, *, user_id: UUID, role: str) -> bool: ...

    async def remove_user_role(self, *, user_id: UUID, role: str) -> bool: ...

    async def record_audit(self, event: DeveloperAdminAuditEvent) -> DeveloperAdminAuditEvent: ...
