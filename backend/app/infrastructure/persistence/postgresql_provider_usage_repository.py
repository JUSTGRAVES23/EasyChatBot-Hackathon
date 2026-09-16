from __future__ import annotations

from src.ai_runtime.providers.usage.models import ProviderUsageEvent
from src.ai_runtime.providers.usage.repository import ProviderUsageRepository

from .provider_usage_records import ProviderUsageRecord


class PostgreSQLProviderUsageRepository(ProviderUsageRepository):
    def __init__(self, session_factory) -> None:
        if session_factory is None:
            raise ValueError("session_factory is required.")

        self._session_factory = session_factory

    def save(self, event: ProviderUsageEvent) -> None:
        if event is None:
            raise ValueError("Provider usage event cannot be None.")

        with self._session_factory() as session:
            session.add(
                ProviderUsageRecord(
                    provider=event.provider,
                    model=event.model,
                    capability=event.capability,
                    functionality=event.functionality,
                    agent=event.agent,
                    input_tokens=event.input_tokens,
                    output_tokens=event.output_tokens,
                    total_tokens=event.total_tokens,
                    latency_ms=event.latency_ms,
                    estimated_cost=event.estimated_cost,
                    quality_score=event.quality_score,
                    success=event.success,
                    provider_request_id=event.provider_request_id,
                    created_at=event.created_at,
                )
            )
            session.commit()

    def get_all(self) -> list[ProviderUsageEvent]:
        with self._session_factory() as session:
            rows = (
                session.query(ProviderUsageRecord)
                .order_by(
                    ProviderUsageRecord.created_at.asc(),
                    ProviderUsageRecord.id.asc(),
                )
                .all()
            )

        return [_event_from_record(row) for row in rows]

    def clear(self) -> None:
        with self._session_factory() as session:
            session.query(ProviderUsageRecord).delete()
            session.commit()


def _event_from_record(row: ProviderUsageRecord) -> ProviderUsageEvent:
    return ProviderUsageEvent(
        provider=row.provider,
        model=row.model,
        capability=row.capability,
        functionality=row.functionality,
        agent=row.agent,
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        total_tokens=row.total_tokens,
        latency_ms=row.latency_ms,
        estimated_cost=row.estimated_cost,
        quality_score=float(row.quality_score),
        success=row.success,
        provider_request_id=row.provider_request_id,
        created_at=row.created_at,
    )
