from __future__ import annotations

from enum import Enum


class OperationsEnvironment(str, Enum):
    KIDS = "kids"
    ADULTS = "adults"


DEFAULT_OPERATIONS_ENVIRONMENT = OperationsEnvironment.ADULTS


def resolve_environment(
    environment: OperationsEnvironment | None,
) -> OperationsEnvironment:
    return environment or DEFAULT_OPERATIONS_ENVIRONMENT
