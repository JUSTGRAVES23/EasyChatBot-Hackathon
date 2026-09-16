from decimal import Decimal

from app.application.provider_management.provider_usage_dashboard_service import (
    ProviderUsageDashboardService,
)
from src.ai_runtime.providers.usage.models import ProviderUsageEvent
from src.ai_runtime.providers.usage.repository import (
    InMemoryProviderUsageRepository,
)


def _event(
    *,
    provider: str = "openai",
    model: str = "gpt-test",
    input_tokens: int | None = 100,
    output_tokens: int | None = 50,
    total_tokens: int | None = 150,
    cost: str = "0.01000000",
    success: bool = True,
) -> ProviderUsageEvent:
    return ProviderUsageEvent(
        provider=provider,
        model=model,
        capability="conversation",
        functionality="chat",
        agent="conversation_agent",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        latency_ms=100,
        estimated_cost=Decimal(cost),
        quality_score=95.0,
        success=success,
        provider_request_id="req-test",
    )


def test_snapshot_aggregates_repository_events() -> None:
    repository = InMemoryProviderUsageRepository()
    repository.save(_event())
    repository.save(
        _event(
            provider="ollama",
            model="gemma-test",
            cost="0",
        )
    )

    service = ProviderUsageDashboardService(
        repository=repository,
    )

    snapshot = service.get_snapshot()

    assert snapshot["total_requests"] == 2
    assert snapshot["successful_requests"] == 2
    assert snapshot["failed_requests"] == 0
    assert snapshot["total_input_tokens"] == 200
    assert snapshot["total_output_tokens"] == 100
    assert snapshot["total_tokens"] == 300
    assert snapshot["total_estimated_cost"] == "0.01000000"
    assert snapshot["by_provider"] == {
        "openai": 1,
        "ollama": 1,
    }


def test_snapshot_preserves_unknown_token_semantics() -> None:
    repository = InMemoryProviderUsageRepository()
    repository.save(
        _event(
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
        )
    )

    service = ProviderUsageDashboardService(
        repository=repository,
    )

    snapshot = service.get_snapshot()

    assert snapshot["total_input_tokens"] is None
    assert snapshot["total_output_tokens"] is None
    assert snapshot["total_tokens"] is None


def test_snapshot_rejects_missing_repository() -> None:
    try:
        ProviderUsageDashboardService(repository=None)  # type: ignore[arg-type]
    except ValueError as exc:
        assert str(exc) == "repository cannot be None."
    else:
        raise AssertionError("Expected ValueError")

