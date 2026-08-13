"""
End-to-end integration test for the Podcast learning flow.

Complete flow:

Podcast Discovery
    |
    v
PodcastDiscoveryExecutor
    |
    v
CapabilityGateway
    |
    v
PodcastRecommendation
    |
    v
Learning Generation
    |
    v
PodcastLearningChallengeExecutor
    |
    v
PodcastLearningChallenge

The test verifies that the output of the Podcast Discovery
capability can be used directly as the input to the Learning
Generation capability.

No external podcast provider is contacted.
"""

import pytest

from src.ai_runtime.capabilities.errors import (
    CapabilityExecutionError,
)

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

from src.ai_runtime.capabilities.podcast_learning_challenge_executor import (
    PodcastLearningChallengeExecutor,
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

from src.ai_runtime.podcast.challenge import (
    PodcastLearningChallenge,
)

from src.ai_runtime.podcast.models import (
    PodcastProviderName,
    PodcastRecommendation,
    PodcastSearchResult,
)


class FakeGovernanceResult:
    """
    Minimal governance result used by the integration test.
    """

    def __init__(
        self,
        allowed: bool,
    ) -> None:
        self.allowed = allowed


class FakeGovernance:
    """
    Deterministic governance implementation.

    Every capability execution must pass through governance.
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
    Deterministic podcast provider.

    This prevents any external Apple or Spotify API call.
    """

    def __init__(self) -> None:
        self.calls = 0

    def search(
        self,
        intent,
    ) -> list[PodcastSearchResult]:
        self.calls += 1

        return [
            PodcastSearchResult(
                provider=PodcastProviderName.APPLE,
                external_id="podcast-flow-001",
                title="L'IA en Europe",
                description=(
                    "Artificial intelligence and "
                    "European regulation in French."
                ),
                publisher="Demo Publisher",
                languages=("fr",),
                url=(
                    "https://example.com/"
                    "podcasts/ia-en-europe"
                ),
                metadata={
                    "learner_level": "B2",
                },
            ),
        ]


def make_memory() -> MemoryEntry:
    """
    Create explicit learner memory for discovery.
    """

    return MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.PREFERENCE,
        content=(
            "Interested in artificial intelligence "
            "and European regulation."
        ),
        metadata={
            "topics": (
                "artificial intelligence, "
                "European regulation"
            ),
        },
    )


def make_discovery_request() -> CapabilityRequest:
    """
    Build the Podcast Discovery Runtime request.
    """

    return CapabilityRequest(
        capability=CapabilityType.PODCAST_DISCOVERY,
        request_id="podcast-flow-discovery-001",
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


def make_learning_request(
    recommendation: PodcastRecommendation,
) -> CapabilityRequest:
    """
    Build the Learning Generation request using the
    actual output of Podcast Discovery.
    """

    return CapabilityRequest(
        capability=CapabilityType.LEARNING_GENERATION,
        request_id="podcast-flow-learning-001",
        payload={
            "recommendation": recommendation,
        },
        requested_by="learning_application",
    )


@pytest.mark.asyncio
async def test_podcast_discovery_output_feeds_learning_generation():
    """
    Verify the complete Discovery → Recommendation →
    Learning Challenge flow.
    """

    provider = FakePodcastProvider()

    discovery_executor = PodcastDiscoveryExecutor(
        agent=PodcastDiscoveryAgent(),
        providers=[
            provider,
        ],
    )

    discovery_registry = CapabilityRegistry(
        executors=[
            discovery_executor,
        ],
    )

    discovery_governance = FakeGovernance(
        allowed=True,
    )

    discovery_gateway = CapabilityGateway(
        registry=discovery_registry,
        governance=discovery_governance,
    )

    discovery_result = (
        await discovery_gateway.execute(
            make_discovery_request(),
        )
    )

    assert (
        discovery_result.status
        == CapabilityExecutionStatus.COMPLETED
    )

    assert discovery_result.succeeded is True

    assert discovery_result.capability == (
        CapabilityType.PODCAST_DISCOVERY
    )

    assert discovery_result.output is not None

    recommendation = discovery_result.output

    assert isinstance(
        recommendation,
        PodcastRecommendation,
    )

    assert recommendation.user_id == (
        "user-001"
    )

    assert recommendation.character_id == (
        "yeti"
    )

    assert recommendation.character_name == (
        "Yeti"
    )

    assert recommendation.result.external_id == (
        "podcast-flow-001"
    )

    assert recommendation.result.title == (
        "L'IA en Europe"
    )

    assert provider.calls == 1

    assert discovery_governance.calls == 1

    learning_executor = (
        PodcastLearningChallengeExecutor()
    )

    learning_registry = CapabilityRegistry(
        executors=[
            learning_executor,
        ],
    )

    learning_governance = FakeGovernance(
        allowed=True,
    )

    learning_gateway = CapabilityGateway(
        registry=learning_registry,
        governance=learning_governance,
    )

    learning_result = (
        await learning_gateway.execute(
            make_learning_request(
                recommendation,
            ),
        )
    )

    assert (
        learning_result.status
        == CapabilityExecutionStatus.COMPLETED
    )

    assert learning_result.succeeded is True

    assert learning_result.capability == (
        CapabilityType.LEARNING_GENERATION
    )

    assert isinstance(
        learning_result.output,
        PodcastLearningChallenge,
    )

    challenge = learning_result.output

    assert challenge.user_id == (
        recommendation.user_id
    )

    assert challenge.podcast_id == (
        recommendation.result.external_id
    )

    assert challenge.podcast_title == (
        recommendation.result.title
    )

    assert challenge.target_language == (
        "fr"
    )

    assert challenge.learner_level == (
        "B2"
    )

    assert challenge.vocabulary

    assert challenge.comprehension_questions

    assert challenge.discussion_prompt

    assert (
        challenge.metadata["content_basis"]
        == "verified_podcast_metadata"
    )

    assert (
        challenge.metadata["challenge_type"]
        == "podcast_learning_mvp"
    )

    assert learning_governance.calls == 1

    assert provider.calls == 1


@pytest.mark.asyncio
async def test_learning_generation_consumes_discovery_result_without_new_search():
    """
    Verify that Learning Generation consumes the existing
    PodcastRecommendation and does not perform another
    podcast provider search.
    """

    provider = FakePodcastProvider()

    discovery_executor = PodcastDiscoveryExecutor(
        agent=PodcastDiscoveryAgent(),
        providers=[
            provider,
        ],
    )

    discovery_gateway = CapabilityGateway(
        registry=CapabilityRegistry(
            executors=[
                discovery_executor,
            ],
        ),
        governance=FakeGovernance(
            allowed=True,
        ),
    )

    discovery_result = (
        await discovery_gateway.execute(
            make_discovery_request(),
        )
    )

    assert discovery_result.succeeded is True

    recommendation = discovery_result.output

    assert isinstance(
        recommendation,
        PodcastRecommendation,
    )

    provider_calls_after_discovery = (
        provider.calls
    )

    learning_executor = (
        PodcastLearningChallengeExecutor()
    )

    learning_gateway = CapabilityGateway(
        registry=CapabilityRegistry(
            executors=[
                learning_executor,
            ],
        ),
        governance=FakeGovernance(
            allowed=True,
        ),
    )

    learning_result = (
        await learning_gateway.execute(
            make_learning_request(
                recommendation,
            ),
        )
    )

    assert learning_result.succeeded is True

    assert (
        provider.calls
        == provider_calls_after_discovery
    )

    assert isinstance(
        learning_result.output,
        PodcastLearningChallenge,
    )


@pytest.mark.asyncio
async def test_discovery_failure_does_not_create_learning_challenge():
    """
    Verify that a rejected Podcast Discovery execution
    cannot produce a Learning Challenge.

    The Gateway wraps executor failures in
    CapabilityExecutionError, so the integration boundary
    asserts that public Runtime error contract.
    """

    discovery_provider = FakePodcastProvider()

    discovery_executor = PodcastDiscoveryExecutor(
        agent=PodcastDiscoveryAgent(),
        providers=[
            discovery_provider,
        ],
    )

    discovery_gateway = CapabilityGateway(
        registry=CapabilityRegistry(
            executors=[
                discovery_executor,
            ],
        ),
        governance=FakeGovernance(
            allowed=False,
        ),
    )

    discovery_result = (
        await discovery_gateway.execute(
            make_discovery_request(),
        )
    )

    assert (
        discovery_result.status
        == CapabilityExecutionStatus.REJECTED
    )

    assert discovery_result.rejected is True

    assert discovery_result.output is None

    learning_executor = (
        PodcastLearningChallengeExecutor()
    )

    learning_gateway = CapabilityGateway(
        registry=CapabilityRegistry(
            executors=[
                learning_executor,
            ],
        ),
        governance=FakeGovernance(
            allowed=True,
        ),
    )

    with pytest.raises(
        CapabilityExecutionError,
        match="Capability executor failed: learning_generation",
    ):
        await learning_gateway.execute(
            make_learning_request(
                discovery_result.output,
            ),
        )