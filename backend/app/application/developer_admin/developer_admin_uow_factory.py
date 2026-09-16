from __future__ import annotations

from typing import Protocol

from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminUnitOfWork,
)


class DeveloperAdminUnitOfWorkFactory(Protocol):
    """Creates a fresh Developer Admin Unit of Work per operation."""

    def create(self) -> DeveloperAdminUnitOfWork:
        """Return a new, unused Unit of Work instance."""
        ...