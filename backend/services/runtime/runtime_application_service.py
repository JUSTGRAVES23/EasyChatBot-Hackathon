"""
Runtime Application Service.

Application boundary for External Runtime execution.

Responsibilities:

- translate application requests into Runtime contracts;
- create CapabilityRequest objects;
- generate request identifiers;
- delegate execution to ExternalRuntimeService;
- return Runtime capability results.

This service does not:

- expose HTTP concerns;
- raise FastAPI HTTP exceptions;
- create providers;
- create agents;
- implement capabilities;
- implement governance;
- bypass Runtime controls.

Architecture:

API
 |
 v
RuntimeApplicationService
 |
 v
ExternalRuntimeService
 |
 v
CapabilityGateway
 |
 v
CapabilityExecutor
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import uuid4

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)

from src.ai_runtime.capabilities.models import (
    CapabilityName,
    CapabilityRequest,
    CapabilityResult,
)


class RuntimeApplicationService:
    """
    Application service for External Runtime execution.

    Keeps API routes thin by moving Runtime
    application orchestration outside HTTP layer.
    """

    def __init__(
        self,
        runtime_service: ExternalRuntimeService,
    ) -> None:
        """
        Initialise RuntimeApplicationService.

        Args:
            runtime_service:
                Configured ExternalRuntimeService.

        Raises:
            ValueError:
                If runtime service is missing.
        """

        if runtime_service is None:
            raise ValueError(
                "ExternalRuntimeService cannot be None."
            )

        self._runtime_service = runtime_service

    async def execute(
        self,
        *,
        capability: str,
        payload: Mapping[str, object],
    ) -> CapabilityResult:
        """
        Execute an External Runtime capability.

        The application layer translates external
        application requests into Runtime contracts.

        Args:

            capability:
                Requested Runtime capability.

            payload:
                Capability execution payload.

        Returns:

            CapabilityResult produced by Runtime.

        Raises:

            ValueError:
                If input is invalid.
        """

        if not isinstance(
            capability,
            str,
        ):
            raise ValueError(
                "Capability must be a string."
            )

        if not capability.strip():
            raise ValueError(
                "Capability cannot be empty."
            )

        if payload is None:
            raise ValueError(
                "Payload cannot be None."
            )

        try:
            capability_name = CapabilityName(
                capability,
            )

        except ValueError as exc:
            raise ValueError(
                f"Unsupported capability: {capability}"
            ) from exc

        execution_payload = {
            "user_id": "demo-user",
            **dict(payload),
        }

        request = CapabilityRequest(
            request_id=str(
                uuid4(),
            ),
            capability=capability_name,
            payload=execution_payload,
        )

        return await self._runtime_service.execute(
            request,
        )