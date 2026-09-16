from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from app.ai_runtime.conversation.conversation_runtime import ConversationRuntime
from app.application.providers.provider_usage_capture import (
    ProviderUsageCapture,
    ProviderUsageContext,
)
from app.infrastructure.persistence.postgresql_provider_usage_repository import (
    PostgreSQLProviderUsageRepository,
)
from app.providers.llm.llm_provider import LLMProvider
from app.providers.provider_result import ProviderResult, ProviderUsage
from app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from src.ai_runtime.providers.usage.service import ProviderUsageService


class FakeProvider(LLMProvider):
    async def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
    ) -> ProviderResult:
        return ProviderResult(
            success=True,
            provider_id="p1_5_4_fake",
            model="deterministic-test-model",
            content="Bonjour depuis le test durable.",
            usage=ProviderUsage(
                input_tokens=17,
                output_tokens=9,
                total_tokens=26,
            ),
            provider_request_id=f"test-{uuid4()}",
            latency_ms=42.0,
            completed_at=datetime.now(timezone.utc),
        )


def _repository_if_table_exists():
    try:
        engine = create_database_engine()
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT to_regclass('public.provider_usage_events')")
            ).scalar()
        if exists is None:
            engine.dispose()
            pytest.skip(
                "provider_usage_events is not migrated yet; "
                "shared database migration remains Academy-owned."
            )
        return engine, create_session_factory(engine)
    except Exception as exc:
        pytest.skip(f"PostgreSQL integration unavailable: {exc}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_provider_result_is_captured_and_persisted_durably():
    engine, session_factory = _repository_if_table_exists()
    repository = PostgreSQLProviderUsageRepository(session_factory)

    capture = ProviderUsageCapture(
        ProviderUsageService(repository)
    )

    runtime = ConversationRuntime(
        llm_provider=FakeProvider(),
        usage_capture=capture,
        usage_context=ProviderUsageContext(
            capability="conversation",
            functionality="chat",
            agent="conversation_agent",
            quality_score=95.0,
            estimated_cost=Decimal("0.00000000"),
        ),
    )

    try:
        result = await runtime.respond(
            character_instruction="Respond in French.",
            learner_message="Bonjour.",
        )

        assert result == "Bonjour depuis le test durable."

        with session_factory() as session:
            row = session.execute(
                text(
                    """
                    SELECT provider, model, capability, functionality,
                           agent, input_tokens, output_tokens,
                           latency_ms, estimated_cost, quality_score, success
                    FROM provider_usage_events
                    WHERE provider = :provider
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
                    """
                ),
                {"provider": "p1_5_4_fake"},
            ).mappings().first()

        assert row is not None
        assert row["provider"] == "p1_5_4_fake"
        assert row["model"] == "deterministic-test-model"
        assert row["capability"] == "conversation"
        assert row["functionality"] == "chat"
        assert row["agent"] == "conversation_agent"
        assert row["input_tokens"] == 17
        assert row["output_tokens"] == 9
        assert row["latency_ms"] == 42
        assert row["estimated_cost"] == Decimal("0E-8")
        assert float(row["quality_score"]) == 95.0
        assert row["success"] is True
    finally:
        repository.clear()
        engine.dispose()

