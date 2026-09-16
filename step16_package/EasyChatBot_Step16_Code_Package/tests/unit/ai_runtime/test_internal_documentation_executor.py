from src.ai_agents.internal_documentation_agent.agent import (
    InternalDocumentationAgent,
)
from src.ai_agents.internal_documentation_agent.models import KnowledgeResult
from src.ai_runtime.capabilities.internal_documentation_executor import (
    InternalDocumentationExecutor,
)


class FakeKnowledgeProvider:
    def search(self, query: str, *, max_results: int = 5):
        return (
            KnowledgeResult(
                source_id="doc-1",
                title="Security Policy",
                content="Internal documentation is read-only for this capability.",
                location="project-brain/security.md",
            ),
        )


def test_executor_returns_structured_results() -> None:
    executor = InternalDocumentationExecutor(
        InternalDocumentationAgent(FakeKnowledgeProvider())
    )

    result = executor.execute(
        {"query": "security policy", "max_results": 5}
    )

    assert result["result_count"] == 1
    assert result["results"][0]["source_id"] == "doc-1"


def test_executor_rejects_non_string_query() -> None:
    executor = InternalDocumentationExecutor(
        InternalDocumentationAgent(FakeKnowledgeProvider())
    )

    try:
        executor.execute({"query": 123})
    except ValueError as exc:
        assert "query" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
