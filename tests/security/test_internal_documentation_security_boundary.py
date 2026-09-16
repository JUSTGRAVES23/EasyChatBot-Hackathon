"""
Security boundary tests for the Internal Documentation capability.

WP16.7 security requirements:

- governance is evaluated before capability execution;
- governance rejection prevents executor execution;
- the Internal Documentation capability is read-only;
- the capability remains isolated behind the governed Runtime boundary.

These tests intentionally exercise the Runtime boundary rather than
testing filesystem implementation details.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from src.ai_agents.internal_documentation_agent.agent import (
    InternalDocumentationAgent,
)
from src.ai_agents.internal_documentation_agent.models import (
    InternalDocumentationRequest,
    InternalDocumentationResponse,
    KnowledgeResult,
)
from src.ai_agents.internal_documentation_agent.knowledge_provider import (
    KnowledgeProvider,
)
from src.ai_runtime.capabilities.executor import (
    CapabilityExecutor,
)
from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)
from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityResult,
    CapabilityType,
)
from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)


# =========================================================
# Test Doubles
# =========================================================


class RecordingKnowledgeProvider:
    """
    Read-only KnowledgeProvider test double.

    Records searches so the tests can prove that a rejected
    capability request never reaches the knowledge layer.
    """

    def __init__(self) -> None:
        self.search_calls: list[tuple[str, int]] = []

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> list[KnowledgeResult]:

        self.search_calls.append(
            (
                query,
                max_results,
            )
        )

        return [
            KnowledgeResult(
                source_id="test-doc-001",
                title="Runtime Architecture",
                content="Runtime capability documentation.",
                location="docs/runtime.md",
                relevance=1.0,
            )
        ]


class RecordingInternalDocumentationAgent:
    """
    Minimal agent double used to prove executor isolation.

    It records whether execution was attempted.
    """

    def __init__(self) -> None:
        self.execute_calls: list[
            InternalDocumentationRequest
        ] = []

    def execute(
        self,
        request: InternalDocumentationRequest,
    ) -> InternalDocumentationResponse:

        self.execute_calls.append(request)

        return InternalDocumentationResponse(
            query=request.query,
            results=(
                KnowledgeResult(
                    source_id="test-doc-001",
                    title="Runtime Architecture",
                    content="Runtime capability documentation.",
                    location="docs/runtime.md",
                    relevance=1.0,
                ),
            ),
        )


class RecordingInternalDocumentationExecutor(
    CapabilityExecutor,
):
    """
    Executor double used to verify that governance rejection
    prevents capability execution.
    """

    def __init__(self) -> None:
        self.execute_calls: list[CapabilityRequest] = []

    @property
    def capability(self) -> CapabilityType:
        return CapabilityType.INTERNAL_DOCUMENTATION_SEARCH

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:

        self.execute_calls.append(request)

        return CapabilityResult(
            request_id=request.request_id,
            capability=self.capability,
            status=CapabilityExecutionStatus.COMPLETED,
            output={
                "result_count": 0,
                "results": [],
            },
        )


@dataclass(frozen=True)
class TestGovernanceDecision:
    """
    Minimal governance decision contract.
    """

    allowed: bool


class ConfigurableGovernance:
    """
    Deterministic governance test double.

    Records evaluation and can explicitly allow or reject
    the capability request.
    """

    def __init__(
        self,
        *,
        allowed: bool,
    ) -> None:

        self.allowed = allowed
        self.evaluate_calls: list[
            CapabilityRequest
        ] = []

    def evaluate(
        self,
        request: CapabilityRequest,
    ) -> TestGovernanceDecision:

        self.evaluate_calls.append(request)

        return TestGovernanceDecision(
            allowed=self.allowed,
        )


# =========================================================
# Helpers
# =========================================================


def build_request() -> CapabilityRequest:
    """
    Create a valid Internal Documentation capability request.
    """

    return CapabilityRequest(
        capability=(
            CapabilityType.INTERNAL_DOCUMENTATION_SEARCH
        ),
        request_id="wp16-security-001",
        payload={
            "query": "runtime capability",
            "max_results": 3,
        },
        metadata={
            "test": "wp16-security",
        },
        requested_by="wp16-security-test",
    )


def build_gateway(
    *,
    executor: CapabilityExecutor,
    governance: Any,
) -> CapabilityGateway:
    """
    Build a governed CapabilityGateway containing only the
    executor required by this security test.
    """

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    return CapabilityGateway(
        registry=registry,
        governance=governance,
    )


# =========================================================
# Governance Ordering
# =========================================================


@pytest.mark.asyncio
async def test_governance_is_evaluated_before_internal_documentation_execution():
    """
    Governance must be evaluated before the executor is invoked.
    """

    executor = RecordingInternalDocumentationExecutor()

    governance = ConfigurableGovernance(
        allowed=True,
    )

    gateway = build_gateway(
        executor=executor,
        governance=governance,
    )

    request = build_request()

    result = await gateway.execute(request)

    assert result.status == (
        CapabilityExecutionStatus.COMPLETED
    )

    assert len(governance.evaluate_calls) == 1
    assert len(executor.execute_calls) == 1

    assert governance.evaluate_calls[0] is request
    assert executor.execute_calls[0] is request


# =========================================================
# Governance Rejection
# =========================================================


@pytest.mark.asyncio
async def test_governance_rejection_prevents_internal_documentation_execution():
    """
    A governance rejection must stop execution before the
    Internal Documentation executor is resolved/executed.
    """

    executor = RecordingInternalDocumentationExecutor()

    governance = ConfigurableGovernance(
        allowed=False,
    )

    gateway = build_gateway(
        executor=executor,
        governance=governance,
    )

    request = build_request()

    result = await gateway.execute(request)

    assert result.status == (
        CapabilityExecutionStatus.REJECTED
    )

    assert result.capability == (
        CapabilityType.INTERNAL_DOCUMENTATION_SEARCH
    )

    assert result.request_id == request.request_id

    assert result.metadata == {
        "governance_decision": "rejected",
    }

    assert len(governance.evaluate_calls) == 1

    # Critical security assertion:
    # the capability executor must never execute after rejection.
    assert executor.execute_calls == []


# =========================================================
# Read-Only Knowledge Boundary
# =========================================================


def test_internal_documentation_agent_uses_read_only_knowledge_provider():
    """
    The Internal Documentation Agent must depend on the
    provider-independent KnowledgeProvider contract.

    The test deliberately provides a provider exposing only
    search(), proving that the Agent does not require write
    operations.
    """

    provider = RecordingKnowledgeProvider()

    agent = InternalDocumentationAgent(
        knowledge_provider=provider,
    )

    response = agent.execute(
        InternalDocumentationRequest(
            query="runtime capability",
            max_results=3,
        )
    )

    assert response.result_count == 1
    assert len(response.results) == 1

    assert provider.search_calls == [
        (
            "runtime capability",
            3,
        )
    ]


# =========================================================
# No External Provider Dependency
# =========================================================


def test_internal_documentation_agent_does_not_require_external_search_provider():
    """
    The Internal Documentation Agent must be constructible
    using only the internal KnowledgeProvider contract.

    This protects the architectural boundary between:

        Internal Documentation
            ↓
        KnowledgeProvider

    and:

        Live Intelligence
            ↓
        External Search Provider
    """

    provider = RecordingKnowledgeProvider()

    agent = InternalDocumentationAgent(
        knowledge_provider=provider,
    )

    assert agent is not None

    response = agent.execute(
        InternalDocumentationRequest(
            query="architecture",
            max_results=1,
        )
    )

    assert response.result_count == 1
    assert provider.search_calls == [
        (
            "architecture",
            1,
        )
    ]


# =========================================================
# Capability Identity
# =========================================================


def test_internal_documentation_executor_exposes_only_approved_capability():
    """
    The executor must identify itself as the explicitly governed
    Internal Documentation capability.
    """

    executor = RecordingInternalDocumentationExecutor()

    assert executor.capability == (
        CapabilityType.INTERNAL_DOCUMENTATION_SEARCH
    )

    assert executor.capability.value == (
        "internal_documentation_search"
    )