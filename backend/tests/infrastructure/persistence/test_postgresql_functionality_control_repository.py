from datetime import datetime, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.infrastructure.persistence.database import Base
from app.infrastructure.persistence.functionality_control_records import (
    FunctionalityControlAuditRecord,
    FunctionalityControlStateRecord,
)
from app.infrastructure.persistence.postgresql_functionality_control_repository import (
    PostgreSQLFunctionalityControlRepository,
)


def create_repository():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(
        engine,
        tables=[
            FunctionalityControlStateRecord.__table__,
            FunctionalityControlAuditRecord.__table__,
        ],
    )

    session_factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return PostgreSQLFunctionalityControlRepository(session_factory), session_factory


def test_missing_functionality_state_defaults_to_enabled():
    repository, _ = create_repository()

    assert repository.get_availability(
        environment="kids",
        functionality_id="conversation",
    ) == "enabled"


def test_record_transition_persists_state_and_audit():
    repository, session_factory = create_repository()
    changed_at = datetime.now(timezone.utc)

    result = repository.record_transition(
        functionality_id="conversation",
        environment="kids",
        availability="disabled",
        action="stop",
        reason="Provider incident",
        changed_at=changed_at,
        changed_by="operator",
    )

    assert result.functionality_id == "conversation"
    assert result.environment == "kids"
    assert result.availability == "disabled"
    assert result.action == "stop"

    assert repository.get_availability(
        environment="kids",
        functionality_id="conversation",
    ) == "disabled"

    last_action = repository.get_last_action(
        environment="kids",
        functionality_id="conversation",
    )

    assert last_action is not None
    assert last_action.action == "stop"
    assert last_action.reason == "Provider incident"
    assert last_action.changed_by == "operator"

    with session_factory() as session:
        audit_count = session.scalar(
            select(func.count())
            .select_from(FunctionalityControlAuditRecord)
        )

        state_count = session.scalar(
            select(func.count())
            .select_from(FunctionalityControlStateRecord)
        )

    assert audit_count == 1
    assert state_count == 1


def test_second_transition_updates_state_and_appends_audit():
    repository, session_factory = create_repository()
    first_time = datetime.now(timezone.utc)

    repository.record_transition(
        functionality_id="telegram",
        environment="adults",
        availability="disabled",
        action="stop",
        reason="Maintenance",
        changed_at=first_time,
        changed_by="operator",
    )

    second_time = datetime.now(timezone.utc)

    repository.record_transition(
        functionality_id="telegram",
        environment="adults",
        availability="enabled",
        action="resume",
        reason=None,
        changed_at=second_time,
        changed_by="admin",
    )

    assert repository.get_availability(
        environment="adults",
        functionality_id="telegram",
    ) == "enabled"

    last_action = repository.get_last_action(
        environment="adults",
        functionality_id="telegram",
    )

    assert last_action is not None
    assert last_action.action == "resume"
    assert last_action.changed_by == "admin"

    with session_factory() as session:
        audit_count = session.scalar(
            select(func.count())
            .select_from(FunctionalityControlAuditRecord)
        )

        state_count = session.scalar(
            select(func.count())
            .select_from(FunctionalityControlStateRecord)
        )

    assert audit_count == 2
    assert state_count == 1

