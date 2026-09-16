from __future__ import annotations

from typing import Any
from uuid import uuid4

from services.external_runtime_service import (
    ExternalRuntimeService,
)

from src.ai_runtime.capabilities.actor_context import RuntimeActorContext
from src.ai_runtime.capabilities.models import (
    CapabilityRequest,
)


class RuntimeApplicationService:
    """
    Application service translating application requests into
    governed Runtime capability requests.

    This service delegates execution to ExternalRuntimeService.

    It does not:

    - access the Runtime container;
    - access the CapabilityGateway directly;
    - select providers;
    - call provider SDKs;
    - implement Runtime governance.
    """

    def __init__(
        self,
        *,
        runtime_service: ExternalRuntimeService,
    ) -> None:

        if runtime_service is None:
            raise ValueError(
                "ExternalRuntimeService cannot be None."
            )

        self._runtime_service = runtime_service

    async def execute(
        self,
        *,
        capability: str,
        payload: dict[str, Any],
        actor: RuntimeActorContext | None = None,
    ) -> Any:
        """
        Validate application input, create a CapabilityRequest,
        and delegate execution to ExternalRuntimeService.
        """

        if (
            not isinstance(capability, str)
            or not capability.strip()
        ):
            raise ValueError(
                "Capability cannot be empty"
            )

        if payload is None:
            raise ValueError(
                "Payload cannot be None"
            )

        if not isinstance(payload, dict):
            raise ValueError(
                "Payload must be a dictionary"
            )

        request = CapabilityRequest(
            capability=capability,
            request_id=str(uuid4()),
            payload=payload,
            requested_by="application",
            actor=actor,
        )

        return await self._runtime_service.execute(
            request,
        )

