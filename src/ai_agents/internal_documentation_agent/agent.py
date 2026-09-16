from __future__ import annotations

from .knowledge_provider import KnowledgeProvider
from .models import InternalDocumentationRequest, InternalDocumentationResponse


class InternalDocumentationAgent:
    """Read-only internal documentation intelligence agent."""

    def __init__(self, knowledge_provider: KnowledgeProvider) -> None:
        self._knowledge_provider = knowledge_provider

    def execute(
        self,
        request: InternalDocumentationRequest,
    ) -> InternalDocumentationResponse:
        results = self._knowledge_provider.search(
            request.query,
            max_results=request.max_results,
        )
        return InternalDocumentationResponse(
            results=tuple(results),
            result_count=len(results),
        )
