"""
Integration tests for Podcast Learning Challenge
through the AI Runtime Gateway.

This verifies:

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
PodcastLearningChallengeExecutor
    |
    v
PodcastLearningChallengeService
    |
    v
PodcastLearningChallenge
    |
    v
CapabilityResult
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

from src.ai_runtime.capabilities.podcast_learning_challenge_executor import (
    PodcastLearningChallengeExecutor,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
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

    The test verifies that governance is evaluated
    before learning generation executes.
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


def make_recommendation() -> PodcastRecommendation:
    """
    Create a verified PodcastRecommendation.

    The learning challenge consumes this existing
    recommendation and does not perform discovery.
    """

    result = PodcastSearchResult(
        provider=PodcastProviderName.APPLE,
        external_id="podcast-001",
        title="L'IA en Europe",
        description=(
            "AI and European regulation in French."
        ),
        publisher="Demo Publisher",
        languages=("fr",),
        url=(
            "https://podcasts.apple.com/"
            "demo/ai-europe"
        ),
        metadata={
            "learner_level": "B2",
        },
    )

    return PodcastRecommendation(
        recommendation_id="recommendation-001",
        user_id="user-001",
        character_id="yeti",
        character_name="Yeti",
        character_message=(
            "I found this for you!"
        ),
        result=result,
        relevance_reason=(
            "It matches your interests."
        ),
        match_score=90,
    )


def make_request() -> CapabilityRequest:
    """
    Build a Runtime Learning Generation request.
    """

    return CapabilityRequest(
        capability=CapabilityType.LEARNING_GENERATION,
        request_id="challenge-gateway-001",
        payload={
            "recommendation": (
                make_recommendation()
            ),
        },
        requested_by="learning_application",
    )


@pytest.mark.asyncio
async def test_podcast_learning_challenge_executes_through_gateway():
    """
    Verify the complete Runtime Gateway flow.
    """

    executor = (
        PodcastLearningChallengeExecutor()
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

    result = await gateway.execute(
        make_request(),
    )

    assert (
        result.status
        == CapabilityExecutionStatus.COMPLETED
    )

    assert result.succeeded is True

    assert result.request_id == (
        "challenge-gateway-001"
    )

    assert result.capability == (
        CapabilityType.LEARNING_GENERATION
    )

    assert isinstance(
        result.output,
        PodcastLearningChallenge,
    )

    challenge = result.output

    assert challenge.user_id == (
        "user-001"
    )

    assert challenge.podcast_id == (
        "podcast-001"
    )

    assert challenge.podcast_title == (
        "L'IA en Europe"
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

    assert governance.calls == 1


@pytest.mark.asyncio
async def test_gateway_uses_registered_learning_generation_executor():
    """
    Verify the Gateway obtains the executor through the
    CapabilityRegistry rather than constructing it itself.
    """

    executor = (
        PodcastLearningChallengeExecutor()
    )

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    resolved = registry.resolve(
        CapabilityType.LEARNING_GENERATION
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

    assert isinstance(
        result.output,
        PodcastLearningChallenge,
    )


@pytest.mark.asyncio
async def test_gateway_rejects_learning_generation_before_execution():
    """
    Verify governance can reject learning generation
    before the challenge executor runs.
    """

    executor = (
        PodcastLearningChallengeExecutor()
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

    result = await gateway.execute(
        make_request(),
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


@pytest.mark.asyncio
async def test_gateway_does_not_perform_podcast_discovery():
    """
    Learning Generation consumes an existing verified
    PodcastRecommendation.

    It must not perform Apple/Spotify discovery.
    """

    executor = (
        PodcastLearningChallengeExecutor()
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

    result = await gateway.execute(
        make_request(),
    )

    assert result.succeeded is True

    challenge = result.output

    assert challenge.podcast_id == (
        "podcast-001"
    )

    assert challenge.metadata[
        "content_basis"
    ] == "verified_podcast_metadata"