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
from app.application.provider_management.environment import (
    OperationsEnvironment,
    resolve_environment,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)


class FunctionalityHealthService:
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

    _CATEGORY_BY_FUNCTIONALITY = {
        "conversation": "AI",
        "telegram": "Communication",
        "voice_tts": "AI",
        "lessons": "Learning",
        "review": "Learning",
        "pdf_presentation": "Content",
        "email_workflows": "Communication",
        "payments": "Platform",
        "authentication": "Platform",
        "scheduler": "Platform",
        "provider_runtime": "Infrastructure",
        "database": "Infrastructure",
    }

    def __init__(
        self,
        *,
        readiness_service: ProductionReadinessService,
        functionality_control_service: FunctionalityOperationalControlService | None = None,
    ) -> None:
        if readiness_service is None:
            raise ValueError("readiness_service cannot be None.")
        self._readiness_service = readiness_service
        self._functionality_control_service = functionality_control_service

    async def get_health(
        self,
        *,
        environment: OperationsEnvironment | None = None,
    ) -> dict[str, Any]:
        resolved_environment = resolve_environment(environment)
        readiness = await self._readiness_service.check()
        checks_by_name = {check.name: check for check in readiness.checks}
        generated_at = datetime.now(timezone.utc).isoformat()

        functionalities = [
            self._build_functionality(
                functionality_id=functionality_id,
                name=name,
                check=self._resolve_check(
                    functionality_id=functionality_id,
                    checks_by_name=checks_by_name,
                ),
                environment=resolved_environment,
                checked_at=generated_at,
                availability=self._get_availability(
                    functionality_id=functionality_id,
                    environment=resolved_environment,
                ),
            )
            for functionality_id, name in self._FUNCTIONALITIES
        ]

        attention = [
            item for item in functionalities
            if item["status"] in {"degraded", "unavailable"}
        ]

        counts = {
            "total": len(functionalities),
            "healthy": sum(item["status"] == "healthy" for item in functionalities),
            "degraded": sum(item["status"] == "degraded" for item in functionalities),
            "incident": sum(item["status"] == "unavailable" for item in functionalities),
            "maintenance": 0,
            "disabled": 0,
            "unknown": sum(item["status"] == "unknown" for item in functionalities),
        }

        if counts["incident"] > 0:
            platform_health, score, impact = "incident", 0.0, "high"
        elif counts["degraded"] > 0:
            platform_health, score, impact = "degraded", 50.0, "medium"
        elif counts["healthy"] > 0:
            platform_health, score, impact = "healthy", 100.0, "low"
        else:
            platform_health, score, impact = "unknown", None, "unknown"

        return {
            "generated_at": generated_at,
            "environment": resolved_environment.value,
            "platform_health": platform_health,
            "platform_health_score": score,
            "user_impact": impact,
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
        for check_name, functionality_ids in cls._CHECK_TO_FUNCTIONALITIES.items():
            if functionality_id in functionality_ids:
                return checks_by_name.get(check_name)
        return None

    @classmethod
    def _build_functionality(
        cls,
        *,
        functionality_id: str,
        name: str,
        check: HealthCheckResult | None,
        environment: OperationsEnvironment,
        checked_at: str,
        availability: str,
    ) -> dict[str, Any]:
        if check is None:
            status = "unknown"
            health_score = None
            risk_level = "unknown"
            provider = model = latency_ms = None
            reason = "No dedicated health check is currently available."
        else:
            status = cls._map_status(check.status)
            health_score = (
                100.0 if status == "healthy"
                else 50.0 if status == "degraded"
                else 0.0 if status == "unavailable"
                else None
            )
            risk_level = {
                "healthy": "low",
                "degraded": "medium",
                "unavailable": "high",
                "unknown": "unknown",
            }[status]
            provider = check.details.get("provider")
            model = check.details.get("model")
            latency_ms = check.details.get("latency_ms")
            reason = check.details.get("reason", "Health check completed.")

        return {
            "functionality_id": functionality_id,
            "name": name,
            "category": cls._CATEGORY_BY_FUNCTIONALITY[functionality_id],
            "description": f"Operational health for {name}.",
            "status": status,
            "health_score": health_score,
            "latency_ms": latency_ms,
            "provider": provider,
            "model": model,
            "capability": functionality_id,
            "checked_at": checked_at,
            "controllable": False,
            "risk_level": risk_level,
            "reason": reason,
            "environment": environment.value,
            "availability": availability,
            "policy_status": "not_evaluated",
        }

    def _get_availability(
        self,
        *,
        functionality_id: str,
        environment: OperationsEnvironment,
    ) -> str:
        if self._functionality_control_service is None:
            return "enabled"

        return self._functionality_control_service.get_availability(
            environment=environment.value,
            functionality_id=functionality_id,
        )

    @staticmethod
    def _map_status(status: HealthStatus) -> str:
        if status is HealthStatus.HEALTHY:
            return "healthy"
        if status is HealthStatus.UNHEALTHY:
            return "unavailable"
        return "unknown"


__all__ = ["FunctionalityHealthService"]









