"""
External Runtime Application Service.

Application-facing boundary for governed Runtime capability execution.

Responsibilities:

- accept application CapabilityRequest instances;
- validate the request;
- delegate execution to the injected CapabilityGateway.

Does NOT:

- compose Runtime dependencies;
- create providers;
- create gateways;
- access the ExternalRuntimeContainer;
- bypass Runtime governance;
- execute providers directly.
"""

from __future__ import annotations

from typing import Any

from src.ai_runtime.capabilities.gateway import CapabilityGateway
from src.ai_runtime.capabilities.models import CapabilityRequest


class ExternalRuntimeService:
    """Application-facing boundary for governed Runtime execution."""

    def __init__(
        self,
        *,
        gateway: CapabilityGateway,
    ) -> None:
        if gateway is None:
            raise ValueError(
                "CapabilityGateway cannot be None"
            )

        self._gateway = gateway

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> Any:
        """
        Delegate a validated application request to the
        canonical CapabilityGateway.

        Args:
            request:
                Application Runtime capability request.

        Raises:
            ValueError:
                If request is None.
        """

        if request is None:
            raise ValueError(
                "CapabilityRequest cannot be None"
            )

        return await self._gateway.execute(request)