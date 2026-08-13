"""
AI Runtime Capability Gateway.

Controlled execution boundary between applications and
concrete AI capabilities.

Flow:

Application
    |
    v
CapabilityRequest
    |
    v
CapabilityGateway
    |
    v
Governance
    |
    v
CapabilityRegistry
    |
    v
CapabilityExecutor
    |
    v
CapabilityResult

The gateway:

- validates execution requests;
- enforces governance before execution;
- resolves registered capabilities;
- delegates execution.

The gateway does not:

- implement capability logic;
- call providers;
- manage memory;
- modify agents;
- perform external side effects.
"""

from __future__ import annotations

from typing import Protocol

from src.ai_runtime.capabilities.errors import (
    CapabilityExecutionError,
    CapabilityGovernanceError,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityResult,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)


class GovernanceDecisionResult(Protocol):
    """
    Minimal governance result required by Runtime.
    """

    @property
    def allowed(self) -> bool:
        """
        Whether execution is permitted.
        """
        ...


class CapabilityGovernance(Protocol):
    """
    Governance boundary required by Runtime gateway.
    """

    def evaluate(
        self,
        request: CapabilityRequest,
    ) -> GovernanceDecisionResult:
        """
        Evaluate whether a capability may execute.
        """
        ...


class CapabilityGateway:
    """
    Controlled Runtime entry point for capability execution.

    Responsibilities:

    - governance enforcement;
    - capability resolution;
    - execution delegation.

    It is intentionally not a business layer.
    """

    def __init__(
        self,
        registry: CapabilityRegistry,
        governance: CapabilityGovernance,
    ) -> None:
        """
        Create capability gateway.

        Dependencies are injected from composition.
        """

        if registry is None:
            raise ValueError(
                "CapabilityRegistry cannot be None."
            )

        if governance is None:
            raise ValueError(
                "CapabilityGovernance cannot be None."
            )

        self._registry = registry
        self._governance = governance

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        """
        Execute an approved capability.

        Execution order:

        1. Validate request
        2. Evaluate governance
        3. Resolve executor
        4. Execute capability

        Governance is always evaluated before
        capability execution.
        """

        if request is None:
            raise ValueError(
                "CapabilityRequest cannot be None."
            )

        try:
            governance_result = (
                self._governance.evaluate(
                    request,
                )
            )

        except Exception as exc:
            raise CapabilityGovernanceError(
                "Governance evaluation failed."
            ) from exc

        if not governance_result.allowed:
            return CapabilityResult(
                request_id=request.request_id,
                capability=request.capability,
                status=(
                    CapabilityExecutionStatus.REJECTED
                ),
                error=(
                    "Capability execution was rejected "
                    "by governance."
                ),
                metadata={
                    "governance_decision": "rejected",
                },
            )

        try:
            executor = self._registry.resolve(
                request.capability,
            )

        except Exception as exc:
            raise CapabilityExecutionError(
                "Capability resolution failed: "
                f"{request.capability.value}"
            ) from exc

        try:
            return await executor.execute(
                request,
            )

        except Exception as exc:
            raise CapabilityExecutionError(
                "Capability executor failed: "
                f"{request.capability.value}"
            ) from exc