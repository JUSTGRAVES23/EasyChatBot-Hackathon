"""
AI Runtime capability registry.

The registry maps logical Runtime capabilities to their
concrete executors.

The registry:
- resolves executors by capability
- prevents duplicate registrations
- provides explicit dependency injection
- does not execute capabilities
- does not perform governance decisions
- does not know about providers
"""

from __future__ import annotations

from src.ai_runtime.capabilities.errors import (
    CapabilityAlreadyRegisteredError,
    CapabilityNotRegisteredError,
)

from src.ai_runtime.capabilities.executor import (
    CapabilityExecutor,
)

from src.ai_runtime.capabilities.models import (
    CapabilityType,
)


class CapabilityRegistry:
    """
    Dependency-injection registry for Runtime capabilities.
    """

    def __init__(
        self,
        executors: list[CapabilityExecutor] | None = None,
    ) -> None:
        self._executors: dict[
            CapabilityType,
            CapabilityExecutor,
        ] = {}

        for executor in executors or []:
            self.register(executor)

    def register(
        self,
        executor: CapabilityExecutor,
    ) -> None:
        """
        Register an executor for its declared capability.
        """

        capability = executor.capability

        if capability in self._executors:
            raise CapabilityAlreadyRegisteredError(
                "Capability executor already registered: "
                f"{capability.value}"
            )

        self._executors[capability] = executor

    def resolve(
        self,
        capability: CapabilityType,
    ) -> CapabilityExecutor:
        """
        Resolve the executor responsible for a capability.
        """

        try:
            return self._executors[capability]
        except KeyError as exc:
            raise CapabilityNotRegisteredError(
                "No executor registered for capability: "
                f"{capability.value}"
            ) from exc

    def contains(
        self,
        capability: CapabilityType,
    ) -> bool:
        """
        Return whether an executor is registered.
        """

        return capability in self._executors

    def capabilities(
        self,
    ) -> tuple[CapabilityType, ...]:
        """
        Return all registered capabilities.
        """

        return tuple(self._executors.keys())