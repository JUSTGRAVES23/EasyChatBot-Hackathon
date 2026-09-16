from datetime import datetime, timezone

from backend.app.application.persistence_operations.environment import (
    PersistenceEnvironmentNotConfigured,
    create_environment_engine_resolver,
)
from backend.app.application.persistence_operations.persistence_diagnostics_service import (
    PersistenceDiagnosticsService,
)
from backend.app.infrastructure.persistence_operations.alembic_diagnostics import (
    _pending_revisions,
)
from backend.app.infrastructure.persistence_operations.postgres_diagnostics import (
    QUERY_TEXT_REDACTION,
    _redact_query,
)


def test_inconsistent_migration_history_blocks_execution():
    recommendation = PersistenceDiagnosticsService._recommend(
        database={"connected": True},
        migration={"graph": "INCONSISTENT", "missing_revisions": ["20260901_missing"]},
        schema={"state": "IN_SYNC", "tables_with_drift": 0},
        compatibility={"state": "COMPATIBLE"},
    )
    assert recommendation["severity"] == "CRITICAL"
    assert recommendation["timing"] == "STOP_DO_NOT_PROCEED"
    assert "Apply migrations" in recommendation["blocked_actions"]


def test_migration_error_is_treated_as_stop_condition():
    recommendation = PersistenceDiagnosticsService._recommend(
        database={"connected": True},
        migration={"graph": "ERROR", "missing_revisions": []},
        schema={"state": "IN_SYNC", "tables_with_drift": 0},
        compatibility={"state": "COMPATIBLE"},
    )
    assert recommendation["severity"] == "CRITICAL"
    assert recommendation["timing"] == "STOP_DO_NOT_PROCEED"


def test_schema_drift_requires_resolution_before_deployment():
    recommendation = PersistenceDiagnosticsService._recommend(
        database={"connected": True},
        migration={"graph": "IN_SYNC", "missing_revisions": []},
        schema={"state": "DRIFT_DETECTED", "tables_with_drift": 1},
        compatibility={"state": "COMPATIBLE"},
    )
    assert recommendation["severity"] == "HIGH"
    assert recommendation["timing"] == "BEFORE_NEXT_DEPLOYMENT"


def test_compatibility_drift_requires_resolution():
    recommendation = PersistenceDiagnosticsService._recommend(
        database={"connected": True},
        migration={"graph": "IN_SYNC", "missing_revisions": []},
        schema={"state": "IN_SYNC", "tables_with_drift": 0},
        compatibility={"state": "OUT_OF_SYNC"},
    )
    assert recommendation["severity"] == "HIGH"
    assert recommendation["timing"] == "BEFORE_NEXT_DEPLOYMENT"


def test_in_sync_persistence_requires_no_action():
    recommendation = PersistenceDiagnosticsService._recommend(
        database={"connected": True},
        migration={"graph": "IN_SYNC", "missing_revisions": []},
        schema={"state": "IN_SYNC", "tables_with_drift": 0},
        compatibility={"state": "COMPATIBLE"},
    )
    assert recommendation["severity"] == "INFO"
    assert recommendation["timing"] == "NO_ACTION_REQUIRED"


def test_single_engine_is_restricted_to_dev():
    resolver = create_environment_engine_resolver({"dev": object()})
    assert resolver("dev") is not None
    try:
        resolver("production")
    except PersistenceEnvironmentNotConfigured:
        pass
    else:
        raise AssertionError("Unconfigured environments must not reuse DEV.")


def test_pending_revisions_respects_branches():
    graph = {
        "aaaa": set(),
        "bbbb": {"aaaa"},
        "cccc": {"aaaa"},
        "dddd": {"bbbb"},
        "eeee": {"cccc"},
    }
    assert _pending_revisions(["dddd", "eeee"], ["bbbb"], graph) == [
        "cccc",
        "dddd",
        "eeee",
    ]
    assert _pending_revisions(["dddd", "eeee"], ["dddd", "eeee"], graph) == []


def test_query_text_is_redacted_by_default(monkeypatch):
    monkeypatch.delenv("PERSISTENCE_EXPOSE_QUERY_TEXT", raising=False)
    assert _redact_query("SELECT secret FROM users") == QUERY_TEXT_REDACTION


def test_query_text_can_be_explicitly_exposed_for_authorised_diagnostics(monkeypatch):
    monkeypatch.setenv("PERSISTENCE_EXPOSE_QUERY_TEXT", "true")
    assert _redact_query("SELECT 1") == "SELECT 1"


def test_schema_drift_detects_unexpected_and_missing_columns():
    from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

    from backend.app.infrastructure.persistence_operations.postgres_diagnostics import (
        inspect_schema,
    )

    metadata = MetaData()
    Table("example", metadata, Column("id", Integer, nullable=False), Column("name", String))
    engine = create_engine("sqlite://")
    Table("example", MetaData(), Column("id", Integer, nullable=False), Column("legacy", String)).create(engine)

    snapshot = inspect_schema(
        engine,
        metadata,
        checked_at=datetime.now(timezone.utc),
    )

    kinds = {difference["kind"] for difference in snapshot["differences"]}
    assert snapshot["state"] == "DRIFT_DETECTED"
    assert "missing-column" in kinds
    assert "unexpected-column" in kinds
