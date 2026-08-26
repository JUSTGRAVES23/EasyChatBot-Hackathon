from __future__ import annotations

from datetime import datetime, timezone

from backend.app.infrastructure.announcements.sqlalchemy_publication_execution_repository import (
    PublicationExecutionRecordModel,
)
from backend.app.infrastructure.persistence.database import Base


def test_execution_model_uses_canonical_application_base() -> None:
    assert issubclass(PublicationExecutionRecordModel, Base)
    assert PublicationExecutionRecordModel.__tablename__ == (
        "announcement_publication_executions"
    )


def test_execution_schema_contains_only_operational_fields() -> None:
    columns = set(PublicationExecutionRecordModel.__table__.columns.keys())

    assert columns == {
        "publication_id",
        "idempotency_key",
        "correlation_id",
        "attempt",
        "status",
        "provider_message_id",
        "error_code",
        "created_at",
        "updated_at",
    }


def test_idempotency_key_is_primary_key() -> None:
    column = PublicationExecutionRecordModel.__table__.c.idempotency_key
    assert column.primary_key is True
    assert column.nullable is False
