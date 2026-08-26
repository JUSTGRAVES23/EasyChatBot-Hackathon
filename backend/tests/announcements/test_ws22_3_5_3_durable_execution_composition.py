from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv

from backend.app.application.announcements.execution.audit_adapter import (
    DurablePublicationExecutionAudit,
)
from backend.app.application.announcements.execution.durable_execution_composition import (
    DurablePublicationExecutionComposition,
    create_durable_publication_execution_composition,
)
from backend.app.application.announcements.execution.durable_execution_service import (
    DurablePublicationExecutionService,
)
from backend.app.infrastructure.announcements.publication_audit_repository import (
    SqlAlchemyPublicationAuditRepository,
)
from backend.app.infrastructure.announcements.sqlalchemy_publication_execution_repository import (
    SqlAlchemyPublicationExecutionRepository,
)


def _load_repository_environment() -> None:
    """Load the repository .env before creating the canonical DB boundary."""

    load_dotenv()

    if not os.getenv("DATABASE_URL"):
        pytest.skip(
            "DATABASE_URL is not configured for PostgreSQL integration tests."
        )


class RecordingPublisher:
    async def publish(self, **kwargs) -> str:
        return "provider-test-001"


@pytest.mark.asyncio
async def test_ws22_composition_uses_canonical_shared_persistence() -> None:
    _load_repository_environment()

    composition = create_durable_publication_execution_composition(
        publisher=RecordingPublisher(),
    )

    try:
        assert isinstance(
            composition,
            DurablePublicationExecutionComposition,
        )

        assert isinstance(
            composition.service,
            DurablePublicationExecutionService,
        )

        assert isinstance(
            composition.execution_repository,
            SqlAlchemyPublicationExecutionRepository,
        )

        assert isinstance(
            composition.audit_repository,
            SqlAlchemyPublicationAuditRepository,
        )

        assert isinstance(
            composition.audit,
            DurablePublicationExecutionAudit,
        )

        # Critical architectural invariant:
        # both WS-22 durable repositories use the canonical shared
        # async session factory.
        assert (
            composition.execution_repository._session_factory
            is composition.session_factory
        )

        assert (
            composition.audit_repository._session_factory
            is composition.session_factory
        )

    finally:
        await composition.dispose()


@pytest.mark.asyncio
async def test_ws22_composition_rejects_missing_publisher() -> None:
    with pytest.raises(ValueError, match="publisher cannot be None"):
        create_durable_publication_execution_composition(
            publisher=None,
        )