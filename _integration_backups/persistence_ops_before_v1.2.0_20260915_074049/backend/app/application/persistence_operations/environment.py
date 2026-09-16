from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


class PersistenceEnvironmentNotConfigured(RuntimeError):
    """Raised when a requested environment has no configured database engine."""


EngineResolver = Callable[[str], Any]


def create_environment_engine_resolver(
    engines: Mapping[str, Any],
) -> EngineResolver:
    """Create an explicit environment -> SQLAlchemy engine resolver.

    Only configured environments are returned. This prevents a DEV engine from
    being silently reused when an operator selects STAGING or PRODUCTION.
    """

    configured = dict(engines)

    def resolve(environment: str) -> Any:
        engine = configured.get(environment)
        if engine is None:
            raise PersistenceEnvironmentNotConfigured(
                f"Persistence environment '{environment}' is not configured."
            )
        return engine

    return resolve
