"""Functionality health aggregation for the Operations Center."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.application.health.health_result import (
    HealthCheckResult,
    HealthStatus,
)
from app.application.health.production_readiness_service import (
    ProductionReadinessService,
)


class FunctionalityHealthService:
    """Build the M1.2 read-only functionality-health projection."""

    _FUNCTIONALITIES = (
        ("conversation", "AI Conversation"),
        ("telegram", "Telegram"),
        ("voice_tts", "Voice / TTS"),
        ("lessons", "Lessons"),
        ("review", "Review / Spaced Repetition"),
        ("pdf_presentation", "PDF / Presentation"),
        ("email_workflows", "Email Workflows"),
        ("payments", "Payments"),
        ("authentication", "Authentication"),
        ("scheduler", "Scheduler"),
        ("provider_runtime", "Provider / LLM Runtime"),
        ("database", "Database"),
    )

    _CHECK_TO_FUNCTIONALITIES = {
        "llm_provider": {"conversation", "provider_runtime"},
        "telegram": {"telegram"},
        "postgresql": {"database"},
    }

    def __init__(
        self,
        *,
        readiness_service: ProductionReadinessService,
    ) -> None:
        if readiness_service is None:
            raise ValueError(
                "readiness_service cannot be None."
            )

        self._readiness_service = readiness_service

    async def get_health(self) -> dict[str, Any]:
        """Execute the existing health checks and build the dashboard view."""

        readiness = await self._readiness_service.check()

        checks_by_name = {
            check.name: check
            for check in readiness.checks
        }

        functionalities = [
            self._build_functionality(
                functionality_id=functionality_id,
                name=name,
                check=self._resolve_check(
                    functionality_id=functionality_id,
                    checks_by_name=checks_by_name,
                ),
            )
            for functionality_id, name in self._FUNCTIONALITIES
        ]

        attention = [
            item
            for item in functionalities
            if item["status"] in {"degraded", "unavailable"}
        ]

        counts = {
            "total": len(functionalities),
            "healthy": sum(
                item["status"] == "healthy"
                for item in functionalities
            ),
            "degraded": sum(
                item["status"] == "degraded"
                for item in functionalities
            ),
            "incident": sum(
                item["status"] == "unavailable"
                for item in functionalities
            ),
            "maintenance": 0,
            "disabled": 0,
            "unknown": sum(
                item["status"] == "unknown"
                for item in functionalities
            ),
        }

        if counts["incident"] > 0:
            platform_health = "incident"
            user_impact = "high"
        elif counts["degraded"] > 0:
            platform_health = "degraded"
            user_impact = "medium"
        elif counts["healthy"] > 0:
            platform_health = "healthy"
            user_impact = "low"
        else:
            platform_health = "unknown"
            user_impact = "unknown"

        return {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "platform_health": platform_health,
            "user_impact": user_impact,
            "counts": counts,
            "functionalities": functionalities,
            "attention": attention,
        }

    @classmethod
    def _resolve_check(
        cls,
        *,
        functionality_id: str,
        checks_by_name: dict[str, HealthCheckResult],
    ) -> HealthCheckResult | None:
        for check_name, functionality_ids in (
            cls._CHECK_TO_FUNCTIONALITIES.items()
        ):
            if functionality_id in functionality_ids:
                return checks_by_name.get(check_name)

        return None

    @staticmethod
    def _build_functionality(
        *,
        functionality_id: str,
        name: str,
        check: HealthCheckResult | None,
    ) -> dict[str, Any]:
        if check is None:
            return {
                "functionality_id": functionality_id,
                "name": name,
                "status": "unknown",
                "health_score": None,
                "risk_level": "unknown",
                "provider": None,
                "model": None,
                "latency_ms": None,
            }

        status = FunctionalityHealthService._map_status(
            check.status
        )

        return {
            "functionality_id": functionality_id,
            "name": name,
            "status": status,
            "health_score": (
                100.0
                if status == "healthy"
                else 50.0
                if status == "degraded"
                else 0.0
                if status == "unavailable"
                else None
            ),
            "risk_level": {
                "healthy": "low",
                "degraded": "medium",
                "unavailable": "high",
                "unknown": "unknown",
            }.get(status, "unknown"),
            "provider": check.details.get("provider"),
            "model": check.details.get("model"),
            "latency_ms": check.details.get("latency_ms"),
        }

    @staticmethod
    def _map_status(
        status: HealthStatus,
    ) -> str:
        if status is HealthStatus.HEALTHY:
            return "healthy"

        if status is HealthStatus.UNHEALTHY:
            return "unavailable"

        if status is HealthStatus.NOT_CONFIGURED:
            return "unknown"

        return "unknown"


__all__ = [
    "FunctionalityHealthService",
]
