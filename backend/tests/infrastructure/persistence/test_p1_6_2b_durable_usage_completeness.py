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
from src.ai_runtime.providers.usage.models import ProviderUsageEvent


def _require_database_url() -> str:
    from dotenv import load_dotenv

    load_dotenv()

    value = os.getenv("DATABASE_URL")

    if not value or not value.startswith("postgresql"):
        pytest.skip("PostgreSQL DATABASE_URL is not configured.")

    return value


def test_repository_round_trips_total_tokens_and_provider_request_id() -> None:
    url = _require_database_url()

    engine = create_engine(
        url,
        pool_pre_ping=True,
    )

    try:
        session_factory = create_session_factory(engine)
        repository = PostgreSQLProviderUsageRepository(session_factory)

        table_exists = engine.connect().execute(
            text(
                "SELECT to_regclass('public.provider_usage_events')"
            )
        ).scalar_one_or_none()

        if table_exists is None:
            pytest.skip(
                "provider_usage_events table is not migrated yet."
            )

        repository.clear()

        event = ProviderUsageEvent(
            provider="p1_6_2b_test_provider",
            model="p1_6_2b_test_model",
            capability="conversation",
            functionality="chat",
            agent="conversation_agent",
            input_tokens=11,
            output_tokens=7,
            total_tokens=18,
            latency_ms=123,
            estimated_cost=Decimal("0.00123456"),
            quality_score=91.5,
            success=True,
            provider_request_id="req-p1-6-2b",
            created_at=datetime.now(timezone.utc),
        )

        repository.save(event)

        restored = repository.get_all()

        assert len(restored) == 1

        restored_event = restored[0]

        assert restored_event.provider == event.provider
        assert restored_event.model == event.model
        assert restored_event.input_tokens == event.input_tokens
        assert restored_event.output_tokens == event.output_tokens
        assert restored_event.total_tokens == event.total_tokens
        assert (
            restored_event.provider_request_id
            == event.provider_request_id
        )
        assert restored_event.latency_ms == event.latency_ms
        assert restored_event.estimated_cost == event.estimated_cost
        assert restored_event.quality_score == event.quality_score
        assert restored_event.success is event.success

    finally:
        engine.dispose()
