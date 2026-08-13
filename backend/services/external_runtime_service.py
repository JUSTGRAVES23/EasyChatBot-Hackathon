"""
External Runtime Application Service.

Provides the application-layer boundary to the external/user-assistance
AI Runtime.

Architecture:

Application
    |
    v
ExternalRuntimeService
    |
    v
CapabilityGateway
    |
    v
CapabilityRegistry
    |
    v
Capability Executor


Responsibilities:

- receive approved capability requests from application services;
- delegate execution to the external Runtime;
- keep API routes independent from Runtime implementation details;
- preserve dependency injection.

This service does not:

- implement capability business logic;
- construct capability executors;
- construct the CapabilityRegistry;
- construct the CapabilityGateway;
- make governance decisions;
- call providers directly;
- execute agents directly;
- modify production systems.

The external Runtime remains responsible for capability execution
and governance enforcement.
"""

from __future__ import annotations


from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_runtime.capabilities.models import (
    CapabilityRequest,
    CapabilityResult,
)


class ExternalRuntimeService:
    """
    Application-layer adapter for the external AI Runtime.

    The CapabilityGateway is injected by the application
    composition layer.

    This keeps the application layer independent from:

    - capability registry;
    - executor implementations;
    - provider integrations.
    """

    def __init__(
        self,
        gateway: CapabilityGateway,
    ) -> None:
        """
        Initialise External Runtime service.

        Args:
            gateway:
                Configured external Runtime gateway.

        Raises:
            ValueError:
                If gateway is missing.
        """

        if gateway is None:
            raise ValueError(
                "CapabilityGateway cannot be None."
            )

        self._gateway = gateway

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        """
        Execute an approved Runtime capability.

        Governance and execution remain delegated to
        CapabilityGateway.

        Args:
            request:
                Explicit Runtime capability request.

        Returns:
            Provider-independent CapabilityResult.

        Raises:
            ValueError:
                If request is missing.
        """

        if request is None:
            raise ValueError(
                "CapabilityRequest cannot be None."
            )

        return await self._gateway.execute(
            request,
        )