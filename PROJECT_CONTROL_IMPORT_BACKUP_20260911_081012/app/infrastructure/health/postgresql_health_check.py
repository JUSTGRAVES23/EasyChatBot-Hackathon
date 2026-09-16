from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.application.health.health_result import (
    HealthCheckResult,
    HealthStatus,
)
from app.infrastructure.persistence.database import (
    create_database_engine,
)


class PostgreSQLHealthCheck:
    """Read-only PostgreSQL connectivity probe.

    Reuses the existing database factory and performs only SELECT 1.
    """

    name = "postgresql"

    def __init__(self, *, engine=None) -> None:
        self._engine = engine

    async def check(self) -> HealthCheckResult:
        owns_engine = self._engine is None
        engine = self._engine or create_database_engine()

        try:
            await asyncio.to_thread(
                self._select_one,
                engine,
            )

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                details={
                    "connectivity": "ok",
                },
            )

        except Exception:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                details={
                    "reason": "database_unavailable",
                },
            )

        finally:
            if owns_engine:
                await asyncio.to_thread(
                    engine.dispose,
                )

    @staticmethod
    def _select_one(engine) -> None:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )


__all__ = [
    "PostgreSQLHealthCheck",
]









