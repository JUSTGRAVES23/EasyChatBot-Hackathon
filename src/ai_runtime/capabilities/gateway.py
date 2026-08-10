"""
AI Runtime Capability Gateway.

Controlled execution boundary between applications and
concrete AI capabilities.

Flow:

Application
    ↓
CapabilityRequest
    ↓
CapabilityGateway
    ↓
Governance
    ↓
CapabilityRegistry
    ↓
CapabilityExecutor
    ↓
CapabilityResult
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
    Minimal governance result required by the Runtime.
    """

    @property
    def allowed(self) -> bool:
        """
        Whether execution is permitted.
        """
        ...


class CapabilityGovernance(Protocol):
    """
    Governance boundary required by the Runtime gateway.
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
    """

    def __init__(
        self,
        registry: CapabilityRegistry,
        governance: CapabilityGovernance,
    ) -> None:
        self._registry = registry
        self._governance = governance

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        """
        Execute an approved capability.

        Governance is evaluated before resolving and executing
        the capability.
        """

        try:
            governance_result = (
                self._governance.evaluate(request)
            )
        except Exception as exc:
            raise CapabilityGovernanceError(
                "Governance evaluation failed."
            ) from exc

        if not governance_result.allowed:
            return CapabilityResult(
                request_id=request.request_id,
                capability=request.capability,
                status=CapabilityExecutionStatus.REJECTED,
                error=(
                    "Capability execution was rejected "
                    "by governance."
                ),
                metadata={
                    "governance_decision": "rejected",
                },
            )

        executor = self._registry.resolve(
            request.capability
        )

        try:
            return await executor.execute(request)
        except Exception as exc:
            raise CapabilityExecutionError(
                "Capability executor failed: "
                f"{request.capability.value}"
            ) from exc