from __future__ import annotations

import importlib.util
from pathlib import Path

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String


MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "alembic"
    / "versions"
    / "20260907_provider_usage_events.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location(
        "provider_usage_migration",
        MIGRATION,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provider_usage_migration_isolated_and_explicit() -> None:
    migration = _load_migration()

    assert migration.revision == "20260907_provider_usage_events"
    assert migration.down_revision is None
    assert migration.branch_labels == ("provider_usage_ledger",)
    assert migration.depends_on is None


def test_provider_usage_record_model_matches_migration_contract() -> None:
    from app.infrastructure.persistence.provider_usage_records import (
        ProviderUsageRecord,
    )

    columns = ProviderUsageRecord.__table__.columns

    assert isinstance(columns["id"].type, BigInteger)

    assert isinstance(columns["provider"].type, String)
    assert columns["provider"].type.length == 64

    assert isinstance(columns["model"].type, String)
    assert columns["model"].type.length == 128

    assert isinstance(columns["input_tokens"].type, Integer)
    assert isinstance(columns["output_tokens"].type, Integer)
    assert isinstance(columns["latency_ms"].type, Integer)

    assert isinstance(columns["estimated_cost"].type, Numeric)
    assert columns["estimated_cost"].type.precision == 18
    assert columns["estimated_cost"].type.scale == 8

    assert isinstance(columns["quality_score"].type, Numeric)
    assert columns["quality_score"].type.precision == 5
    assert columns["quality_score"].type.scale == 2

    assert isinstance(columns["success"].type, Boolean)

    assert isinstance(columns["created_at"].type, DateTime)
    assert columns["created_at"].type.timezone is True