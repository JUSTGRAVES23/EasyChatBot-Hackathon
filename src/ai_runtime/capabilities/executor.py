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
    +---- Podcast Discovery Executor
    +---- Learning Executor
    +---- Evaluation Executor
    +---- Future Executors

The Runtime depends on this contract.

It does not depend directly on:

- agents;
- providers;
- SDKs;
- external APIs.

Concrete executors are responsible for translating the
provider-independent CapabilityRequest into the appropriate
capability implementation.

This module defines contracts only.

It does not:

- execute capabilities;
- call providers;
- apply governance;
- manage runtime state.
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

    Each concrete executor must:

    - declare the capability it handles;
    - implement asynchronous execution;
    - return a provider-independent result.

    Executors must not bypass:

        CapabilityGateway
            |
            v
        Governance
    """

    @property
    @abstractmethod
    def capability(
        self,
    ) -> CapabilityType:
        """
        Return the capability handled by this executor.

        Returns:

            CapabilityType
        """

        raise NotImplementedError(
            "Capability must be implemented."
        )

    @abstractmethod
    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        """
        Execute a capability request.

        Implementations must:

        - consume CapabilityRequest;
        - return CapabilityResult;
        - remain provider-independent.

        Implementations must not:

        - bypass Runtime governance;
        - directly modify application state;
        - create uncontrolled external side effects.
        """

        raise NotImplementedError(
            "Executor execution must be implemented."
        )