from __future__ import annotations

import pytest

from src.ai_agents.internal_documentation_agent.agent import (
    InternalDocumentationAgent,
)
from src.ai_runtime.capabilities.internal_documentation_executor import (
    InternalDocumentationExecutor,
)
from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityType,
)


class FakeKnowledgeProvider:
    def search(self, query: str, max_results: int = 5):
        return [
            type(
                "KnowledgeResult",
                (),
                {
                    "source_id": "doc-1",
                    "title": "Security Policy",
                    "content": "Security policy content",
                    "location": "docs/security.md",
                    "relevance": 0.95,
                },
            )()
        ]


def _request(payload: dict) -> CapabilityRequest:
    return CapabilityRequest(
        capability=CapabilityType.INTERNAL_DOCUMENTATION_SEARCH,
        request_id="test-request-1",
        payload=payload,
    )


@pytest.mark.asyncio
async def test_executor_returns_structured_results() -> None:
    executor = InternalDocumentationExecutor(
        InternalDocumentationAgent(FakeKnowledgeProvider())
    )

    result = await executor.execute(
        _request(
            {
                "query": "security policy",
                "max_results": 5,
            }
        )
    )

    assert result.status == CapabilityExecutionStatus.COMPLETED
    assert result.request_id == "test-request-1"
    assert (
        result.capability
        == CapabilityType.INTERNAL_DOCUMENTATION_SEARCH
    )

    assert result.output["result_count"] == 1
    assert result.output["results"][0]["source_id"] == "doc-1"
    assert result.output["results"][0]["title"] == "Security Policy"


@pytest.mark.asyncio
async def test_executor_rejects_non_string_query() -> None:
    executor = InternalDocumentationExecutor(
        InternalDocumentationAgent(FakeKnowledgeProvider())
    )

    with pytest.raises(ValueError, match="query"):
        await executor.execute(
            _request(
                {
                    "query": 123,
                }
            )
        )


@pytest.mark.asyncio
async def test_executor_rejects_empty_query() -> None:
    executor = InternalDocumentationExecutor(
        InternalDocumentationAgent(FakeKnowledgeProvider())
    )

    with pytest.raises(ValueError, match="query"):
        await executor.execute(
            _request(
                {
                    "query": "   ",
                }
            )
        )


@pytest.mark.asyncio
async def test_executor_rejects_invalid_max_results() -> None:
    executor = InternalDocumentationExecutor(
        InternalDocumentationAgent(FakeKnowledgeProvider())
    )

    with pytest.raises(ValueError, match="max_results"):
        await executor.execute(
            _request(
                {
                    "query": "security",
                    "max_results": "5",
                }
            )
        )
