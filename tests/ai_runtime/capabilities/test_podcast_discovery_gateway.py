"""
Integration tests for Podcast Discovery through the AI Runtime Gateway.

This verifies the complete Runtime path:

CapabilityRequest
    |
    v
CapabilityGateway
    |
    v
Governance
    |
    v
CapabilityRegistry
    |
    v
PodcastDiscoveryExecutor
    |
    v
PodcastDiscoveryAgent
    |
    v
PodcastRecommendationService
    |
    v
CapabilityResult

The test deliberately uses a fake provider so no external
Apple or Spotify API is called.
"""

import pytest

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityType,
)

from src.ai_runtime.capabilities.podcast_discovery_executor import (
    PodcastDiscoveryExecutor,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)

from src.ai_runtime.memory.models import (
    MemoryEntry,
    MemoryType,
)

from src.ai_runtime.podcast.agent import (
    PodcastDiscoveryAgent,
)

from src.ai_runtime.podcast.models import (
    LearningContext,
    PodcastProviderName,
    PodcastSearchResult,
)


class FakeGovernanceResult:
    """
    Minimal governance result for the integration test.
    """

    def __init__(
        self,
        allowed: bool,
    ) -> None:
        self.allowed = allowed


class FakeGovernance:
    """
    Deterministic governance implementation.

    The test verifies that the Runtime governance boundary
    is evaluated before Podcast Discovery execution.
    """

    def __init__(
        self,
        allowed: bool = True,
    ) -> None:
        self.allowed = allowed
        self.calls = 0

    def evaluate(
        self,
        request: CapabilityRequest,
    ) -> FakeGovernanceResult:
        self.calls += 1

        return FakeGovernanceResult(
            allowed=self.allowed,
        )


class FakePodcastProvider:
    """
    Provider fake used to prevent external API calls.

    This implements the existing PodcastProvider contract.
    """

    def __init__(self) -> None:
        self.calls = 0
        self.last_intent = None

    def search(
        self,
        intent,
    ) -> list[PodcastSearchResult]:
        self.calls += 1
        self.last_intent = intent

        return [
            PodcastSearchResult(
                provider=PodcastProviderName.APPLE,
                external_id="podcast-gateway-001",
                title="IA en Europe",
                description=(
                    "Artificial intelligence and European "
                    "regulation in French."
                ),
                publisher="Demo Publisher",
                languages=("fr",),
                url=(
                    "https://example.com/podcast/"
                    "ia-en-europe"
                ),
                metadata={
                    "learner_level": "B2",
                },
            ),
        ]


def make_memory() -> MemoryEntry:
    """
    Create an explicit learner preference memory.

    Memory is supplied to the Runtime capability payload;
    the PodcastDiscoveryExecutor does not retrieve it itself.
    """

    return MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.PREFERENCE,
        content=(
            "Prefers artificial intelligence "
            "and European regulation."
        ),
        metadata={
            "topics": (
                "artificial intelligence, "
                "European regulation"
            ),
        },
    )


def make_request() -> CapabilityRequest:
    """
    Build a realistic Podcast Discovery Runtime request.
    """

    return CapabilityRequest(
        capability=CapabilityType.PODCAST_DISCOVERY,
        request_id="podcast-gateway-001",
        payload={
            "user_id": "user-001",
            "world_id": "French World",
            "target_language": "fr",
            "learner_level": "B2",
            "learning_goal": (
                "Learn French through current affairs."
            ),
            "country_code": "LU",
            "memories": [
                make_memory(),
            ],
            "character_id": "yeti",
            "character_name": "Yeti",
            "character_message": (
                "I found this podcast for you!"
            ),
            "max_results": 10,
        },
        requested_by="learning_application",
    )


@pytest.mark.asyncio
async def test_podcast_discovery_executes_through_runtime_gateway():
    """
    Verify the complete Runtime → Podcast Discovery flow.
    """

    provider = FakePodcastProvider()

    executor = PodcastDiscoveryExecutor(
        agent=PodcastDiscoveryAgent(),
        providers=[provider],
    )

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    governance = FakeGovernance(
        allowed=True,
    )

    gateway = CapabilityGateway(
        registry=registry,
        governance=governance,
    )

    request = make_request()

    result = await gateway.execute(
        request,
    )

    assert (
        result.status
        == CapabilityExecutionStatus.COMPLETED
    )

    assert result.succeeded is True

    assert result.request_id == (
        "podcast-gateway-001"
    )

    assert result.capability == (
        CapabilityType.PODCAST_DISCOVERY
    )

    assert result.output is not None

    recommendation = result.output

    assert recommendation.user_id == (
        "user-001"
    )

    assert recommendation.character_id == (
        "yeti"
    )

    assert recommendation.character_name == (
        "Yeti"
    )

    assert recommendation.result.title == (
        "IA en Europe"
    )

    assert recommendation.result.languages == (
        "fr",
    )

    assert (
        recommendation.match_score
        > 0
    )

    assert (
        "artificial intelligence"
        in recommendation.relevance_reason.lower()
    )

    assert (
        "French World"
        in recommendation.relevance_reason
    )

    assert governance.calls == 1

    assert provider.calls == 1


@pytest.mark.asyncio
async def test_podcast_discovery_gateway_passes_memory_preferences_to_agent():
    """
    Verify that explicit learner memory reaches the Podcast Agent
    through the Runtime payload and affects the resulting search intent.
    """

    provider = FakePodcastProvider()

    executor = PodcastDiscoveryExecutor(
        agent=PodcastDiscoveryAgent(),
        providers=[provider],
    )

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    gateway = CapabilityGateway(
        registry=registry,
        governance=FakeGovernance(
            allowed=True,
        ),
    )

    request = make_request()

    result = await gateway.execute(
        request,
    )

    assert result.succeeded is True

    assert provider.last_intent is not None

    assert provider.last_intent.user_id == (
        "user-001"
    )

    assert (
        "artificial intelligence"
        in provider.last_intent.topics
    )

    assert (
        "European regulation"
        in provider.last_intent.topics
    )

    assert (
        "French World"
        in provider.last_intent.topics
    )

    assert (
        provider.last_intent.learning_context.target_language
        == "fr"
    )

    assert (
        provider.last_intent.learning_context.learner_level
        == "B2"
    )

    assert (
        provider.last_intent.language_required
        is True
    )


@pytest.mark.asyncio
async def test_podcast_discovery_gateway_rejects_before_provider_execution():
    """
    Verify governance blocks Podcast Discovery before the
    executor/provider can execute.
    """

    provider = FakePodcastProvider()

    executor = PodcastDiscoveryExecutor(
        agent=PodcastDiscoveryAgent(),
        providers=[provider],
    )

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    governance = FakeGovernance(
        allowed=False,
    )

    gateway = CapabilityGateway(
        registry=registry,
        governance=governance,
    )

    request = make_request()

    result = await gateway.execute(
        request,
    )

    assert (
        result.status
        == CapabilityExecutionStatus.REJECTED
    )

    assert result.rejected is True

    assert (
        result.metadata["governance_decision"]
        == "rejected"
    )

    assert governance.calls == 1

    assert provider.calls == 0


@pytest.mark.asyncio
async def test_podcast_discovery_gateway_uses_registered_executor():
    """
    Verify that the Gateway obtains Podcast Discovery through
    CapabilityRegistry rather than directly constructing the executor.
    """

    provider = FakePodcastProvider()

    executor = PodcastDiscoveryExecutor(
        agent=PodcastDiscoveryAgent(),
        providers=[provider],
    )

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    resolved = registry.resolve(
        CapabilityType.PODCAST_DISCOVERY
    )

    assert resolved is executor

    gateway = CapabilityGateway(
        registry=registry,
        governance=FakeGovernance(
            allowed=True,
        ),
    )

    result = await gateway.execute(
        make_request(),
    )

    assert result.succeeded is True

    assert provider.calls == 1