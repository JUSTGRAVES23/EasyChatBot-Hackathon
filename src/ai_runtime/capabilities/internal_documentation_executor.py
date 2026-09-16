from __future__ import annotations

from src.ai_agents.internal_documentation_agent.agent import (
    InternalDocumentationAgent,
)
from src.ai_agents.internal_documentation_agent.models import (
    InternalDocumentationRequest,
)
from src.ai_runtime.capabilities.executor import (
    CapabilityExecutor,
)
from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityResult,
    CapabilityType,
)


class InternalDocumentationExecutor(CapabilityExecutor):
    """Runtime executor for internal documentation search."""

    @property
    def capability(self) -> CapabilityType:
        return CapabilityType.INTERNAL_DOCUMENTATION_SEARCH

    def __init__(
        self,
        agent: InternalDocumentationAgent,
    ) -> None:
        if agent is None:
            raise ValueError(
                "InternalDocumentationAgent cannot be None."
            )

        self._agent = agent

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        if request is None:
            raise ValueError(
                "CapabilityRequest cannot be None."
            )

        payload = request.payload

        query = payload.get("query")
        max_results = payload.get("max_results", 5)

        if not isinstance(query, str):
            raise ValueError("query must be a string")

        if not query.strip():
            raise ValueError("query cannot be empty")

        if not isinstance(max_results, int):
            raise ValueError(
                "max_results must be an integer"
            )

        response = self._agent.execute(
            InternalDocumentationRequest(
                query=query,
                max_results=max_results,
            )
        )

        return CapabilityResult(
            request_id=request.request_id,
            capability=self.capability,
            status=CapabilityExecutionStatus.COMPLETED,
            output={
                "result_count": response.result_count,
                "results": [
                    {
                        "source_id": result.source_id,
                        "title": result.title,
                        "content": result.content,
                        "location": result.location,
                        "relevance": result.relevance,
                    }
                    for result in response.results
                ],
            },
        )
