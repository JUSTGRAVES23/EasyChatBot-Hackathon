from __future__ import annotations

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
from src.ai_runtime.providers.usage.aggregation import (
    ProviderUsageAggregationService,
)
from src.ai_runtime.providers.usage.models import ProviderUsageEvent


def _database_url() -> str:
    from pathlib import Path

    from dotenv import dotenv_values

    values = dotenv_values(Path(".env"))
    url = values.get("DATABASE_URL")

    if not url:
        pytest.skip("DATABASE_URL is not configured.")

    if not url.startswith(
        ("postgresql://", "postgresql+psycopg2://")
    ):
        pytest.skip("PostgreSQL DATABASE_URL is not configured.")

    return url


def test_repository_events_can_be_aggregated_from_durable_ledger() -> None:
    engine = create_engine(_database_url())
    session_factory = create_session_factory(engine)
    repository = PostgreSQLProviderUsageRepository(session_factory)

    table_exists = False

    try:
        with engine.connect() as connection:
            table_exists = (
                connection.execute(
                    text(
                        "SELECT to_regclass("
                        "'public.provider_usage_events'"
                        ")"
                    )
                ).scalar()
                is not None
            )

        if not table_exists:
            pytest.skip(
                "provider_usage_events table is not present; "
                "Academy-owned migration handoff is required."
            )

        repository.clear()

        created_at = datetime.now(timezone.utc)

        repository.save(
            ProviderUsageEvent(
                provider="openai",
                model="gpt-5-mini",
                capability="conversation",
                functionality="chat",
                agent="conversation_agent",
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                latency_ms=100,
                estimated_cost=Decimal("0.0035"),
                quality_score=90,
                success=True,
                provider_request_id="p1-6-4c-1",
                created_at=created_at,
            )
        )

        repository.save(
            ProviderUsageEvent(
                provider="openai",
                model="gpt-5-mini",
                capability="conversation",
                functionality="chat",
                agent="conversation_agent",
                input_tokens=500,
                output_tokens=250,
                total_tokens=750,
                latency_ms=120,
                estimated_cost=Decimal("0.00175"),
                quality_score=90,
                success=True,
                provider_request_id="p1-6-4c-2",
                created_at=created_at,
            )
        )

        repository.save(
            ProviderUsageEvent(
                provider="ollama",
                model="local-model",
                capability="conversation",
                functionality="chat",
                agent="conversation_agent",
                input_tokens=200,
                output_tokens=100,
                total_tokens=300,
                latency_ms=80,
                estimated_cost=Decimal("0"),
                quality_score=90,
                success=True,
                provider_request_id=None,
                created_at=created_at,
            )
        )

        events = repository.get_all()

        aggregation = ProviderUsageAggregationService().aggregate(events)

        assert aggregation.total_requests == 3
        assert aggregation.successful_requests == 3
        assert aggregation.failed_requests == 0

        assert aggregation.total_input_tokens == 1700
        assert aggregation.total_output_tokens == 850
        assert aggregation.total_tokens == 2550

        assert aggregation.total_estimated_cost == Decimal("0.00525")

        assert aggregation.by_provider == {
            "openai": 2,
            "ollama": 1,
        }

        assert aggregation.by_model == {
            "gpt-5-mini": 2,
            "local-model": 1,
        }

        assert aggregation.by_capability == {
            "conversation": 3,
        }

        assert aggregation.by_functionality == {
            "chat": 3,
        }

        assert aggregation.by_agent == {
            "conversation_agent": 3,
        }

    finally:
        if table_exists:
            repository.clear()

        engine.dispose()

