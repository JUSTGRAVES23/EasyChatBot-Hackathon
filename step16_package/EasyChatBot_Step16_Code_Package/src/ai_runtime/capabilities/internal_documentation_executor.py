from __future__ import annotations

from typing import Any

from src.ai_agents.internal_documentation_agent.agent import (
    InternalDocumentationAgent,
)
from src.ai_agents.internal_documentation_agent.models import (
    InternalDocumentationRequest,
)


class InternalDocumentationExecutor:
    """Runtime boundary for the internal documentation capability."""

    def __init__(self, agent: InternalDocumentationAgent) -> None:
        self._agent = agent

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = payload.get("query")
        max_results = payload.get("max_results", 5)

        if not isinstance(query, str):
            raise ValueError("query must be a string")
        if not isinstance(max_results, int):
            raise ValueError("max_results must be an integer")

        response = self._agent.execute(
            InternalDocumentationRequest(
                query=query,
                max_results=max_results,
            )
        )

        return {
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
        }
