"""
AI Runtime capability execution contract.

This module defines the interface between the AI Runtime
and concrete capability executors.

Architecture:

AI Runtime
    |
    v
Capability Executor Interface
    |
    +---- Live Intelligence Executor
    +---- Learning Executor
    +---- Evaluation Executor
    +---- Future Executors

The Runtime depends on this contract.

It does not depend directly on:
- agents
- providers
- SDKs
- external APIs

Concrete executors are responsible for translating the
provider-independent CapabilityRequest into the appropriate
capability implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.ai_runtime.capabilities.models import (
    CapabilityRequest,
    CapabilityResult,
    CapabilityType,
)


class CapabilityExecutor(ABC):
    """
    Abstract executor for one Runtime capability.

    Each concrete executor must declare which capability
    it handles and implement asynchronous execution.
    """

    @property
    @abstractmethod
    def capability(self) -> CapabilityType:
        """
        Return the capability handled by this executor.
        """
        raise NotImplementedError

    @abstractmethod
    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        """
        Execute a capability request.

        Implementations must return a provider-independent
        CapabilityResult.

        They must not bypass the Runtime governance boundary.
        """
        raise NotImplementedError