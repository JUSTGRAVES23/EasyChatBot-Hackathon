from src.ai_agents.internal_documentation_agent.agent import (
    InternalDocumentationAgent,
)
from src.ai_agents.internal_documentation_agent.models import (
    InternalDocumentationRequest,
    KnowledgeResult,
)


class FakeKnowledgeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, *, max_results: int = 5):
        self.calls.append((query, max_results))
        return (
            KnowledgeResult(
                source_id="doc-1",
                title="Runtime Architecture",
                content="Input -> Application -> Runtime -> Agent -> Provider -> Result",
                location="project-brain/runtime.md",
                relevance=0.98,
            ),
        )


def test_agent_returns_governed_knowledge_results() -> None:
    provider = FakeKnowledgeProvider()
    agent = InternalDocumentationAgent(provider)

    response = agent.execute(
        InternalDocumentationRequest(
            query="approved Runtime architecture",
            max_results=3,
        )
    )

    assert response.result_count == 1
    assert response.results[0].source_id == "doc-1"
    assert provider.calls == [("approved Runtime architecture", 3)]


def test_request_rejects_empty_query() -> None:
    try:
        InternalDocumentationRequest(query=" ")
    except ValueError as exc:
        assert "query" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
