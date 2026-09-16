from __future__ import annotations

from src.ai_agents.internal_documentation_agent.agent import (
    InternalDocumentationAgent,
)
from src.ai_runtime.capabilities.internal_documentation_executor import (
    InternalDocumentationExecutor,
)
from src.ai_runtime.capabilities.models import (
    CapabilityType,
)
from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)


class FakeKnowledgeProvider:
    def search(self, query: str, *, max_results: int = 5):
        return []


def test_internal_documentation_executor_declares_capability() -> None:
    executor = InternalDocumentationExecutor(
        InternalDocumentationAgent(FakeKnowledgeProvider())
    )

    assert (
        executor.capability
        == CapabilityType.INTERNAL_DOCUMENTATION_SEARCH
    )


def test_internal_documentation_capability_can_be_registered_and_resolved() -> None:
    executor = InternalDocumentationExecutor(
        InternalDocumentationAgent(FakeKnowledgeProvider())
    )

    registry = CapabilityRegistry(
        executors=[executor]
    )

    assert registry.contains(
        CapabilityType.INTERNAL_DOCUMENTATION_SEARCH
    )

    assert (
        registry.resolve(
            CapabilityType.INTERNAL_DOCUMENTATION_SEARCH
        )
        is executor
    )


def test_internal_documentation_capability_is_not_registered_without_executor() -> None:
    registry = CapabilityRegistry()

    assert not registry.contains(
        CapabilityType.INTERNAL_DOCUMENTATION_SEARCH
    )
