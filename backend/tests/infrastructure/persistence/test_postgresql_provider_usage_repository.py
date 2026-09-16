from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text

from app.infrastructure.persistence.database import (
    create_session_factory,
)
from app.infrastructure.persistence.postgresql_provider_usage_repository import (
    PostgreSQLProviderUsageRepository,
)
from app.infrastructure.persistence.provider_usage_records import (
    ProviderUsageRecord,
)
from src.ai_runtime.providers.usage.models import ProviderUsageEvent


def _require_database_url() -> str:
    from dotenv import load_dotenv

    load_dotenv()

    value = os.getenv("DATABASE_URL")
    if not value or not value.startswith("postgresql"):
        pytest.skip("PostgreSQL DATABASE_URL is not configured.")
    return value


def _event() -> ProviderUsageEvent:
    return ProviderUsageEvent(
        provider="p1_4_test_provider",
        model="p1_4_test_model",
        capability="conversation",
        functionality="chat",
        agent="conversation_agent",
        input_tokens=11,
        output_tokens=7,
        latency_ms=123,
        estimated_cost=Decimal("0.00123456"),
        quality_score=91.5,
        success=True,
        created_at=datetime.now(timezone.utc),
    )


def test_repository_uses_canonical_session_boundary():
    url = _require_database_url()
    engine = create_engine(url, pool_pre_ping=True)
    try:
        session_factory = create_session_factory(engine)
        repository = PostgreSQLProviderUsageRepository(session_factory)
        assert repository._session_factory is session_factory
    finally:
        engine.dispose()


def test_repository_round_trips_usage_event_against_postgresql():
    url = _require_database_url()
    engine = create_engine(url, pool_pre_ping=True)
    try:
        session_factory = create_session_factory(engine)
        repository = PostgreSQLProviderUsageRepository(session_factory)

        # P1.4.1 deliberately does not create/drop schema. The migration
        # is a separate P1.4.2 step.
        table_exists = engine.connect().execute(
            text(
                "SELECT to_regclass('public.provider_usage_events')"
            )
        ).scalar_one_or_none()

        if table_exists is None:
            pytest.skip(
                "provider_usage_events table is not migrated yet; "
                "P1.4.2 migration is intentionally separate."
            )

        repository.clear()
        event = _event()
        repository.save(event)

        rows = repository.get_all()
        assert len(rows) == 1
        restored = rows[0]
        assert restored.provider == event.provider
        assert restored.model == event.model
        assert restored.input_tokens == event.input_tokens
        assert restored.output_tokens == event.output_tokens
        assert restored.latency_ms == event.latency_ms
        assert restored.estimated_cost == event.estimated_cost
        assert restored.quality_score == event.quality_score
        assert restored.success is True
    finally:
        engine.dispose()

