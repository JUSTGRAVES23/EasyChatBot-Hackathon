"""
Tests for the AI Runtime capability registry.
"""

import pytest

from src.ai_runtime.capabilities.errors import (
    CapabilityAlreadyRegisteredError,
    CapabilityNotRegisteredError,
)

from src.ai_runtime.capabilities.executor import (
    CapabilityExecutor,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityResult,
    CapabilityType,
)

from src.ai_runtime.capabilities.podcast_learning_challenge_executor import (
    PodcastLearningChallengeExecutor,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)


class FakeLiveIntelligenceExecutor(CapabilityExecutor):
    """
    Fake executor used to test dependency injection.
    """

    @property
    def capability(self) -> CapabilityType:
        return CapabilityType.LIVE_INTELLIGENCE

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            status=CapabilityExecutionStatus.COMPLETED,
            output={"ok": True},
        )


class FakePodcastDiscoveryExecutor(CapabilityExecutor):
    """
    Fake Podcast Discovery executor used only to verify
    Runtime capability registration.

    The real PodcastDiscoveryExecutor is tested separately.
    """

    @property
    def capability(self) -> CapabilityType:
        return CapabilityType.PODCAST_DISCOVERY

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            status=CapabilityExecutionStatus.COMPLETED,
            output={
                "podcast": "test-podcast",
            },
        )


class FakeEvaluationExecutor(CapabilityExecutor):
    """
    Second fake executor used to verify multiple
    capability registrations.
    """

    @property
    def capability(self) -> CapabilityType:
        return CapabilityType.EVALUATION

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            status=CapabilityExecutionStatus.COMPLETED,
            output={"evaluated": True},
        )


def test_registry_registers_executor():
    executor = FakeLiveIntelligenceExecutor()

    registry = CapabilityRegistry()

    registry.register(executor)

    assert registry.contains(
        CapabilityType.LIVE_INTELLIGENCE
    )


def test_registry_registers_podcast_discovery_executor():
    executor = FakePodcastDiscoveryExecutor()

    registry = CapabilityRegistry()

    registry.register(executor)

    assert registry.contains(
        CapabilityType.PODCAST_DISCOVERY
    )


def test_registry_registers_podcast_learning_challenge_executor():
    executor = PodcastLearningChallengeExecutor()

    registry = CapabilityRegistry()

    registry.register(executor)

    assert registry.contains(
        CapabilityType.LEARNING_GENERATION
    )


def test_registry_resolves_registered_executor():
    executor = FakeLiveIntelligenceExecutor()

    registry = CapabilityRegistry(
        executors=[executor]
    )

    resolved = registry.resolve(
        CapabilityType.LIVE_INTELLIGENCE
    )

    assert resolved is executor


def test_registry_resolves_podcast_discovery_executor():
    executor = FakePodcastDiscoveryExecutor()

    registry = CapabilityRegistry(
        executors=[executor]
    )

    resolved = registry.resolve(
        CapabilityType.PODCAST_DISCOVERY
    )

    assert resolved is executor


def test_registry_resolves_podcast_learning_challenge_executor():
    executor = PodcastLearningChallengeExecutor()

    registry = CapabilityRegistry(
        executors=[executor]
    )

    resolved = registry.resolve(
        CapabilityType.LEARNING_GENERATION
    )

    assert resolved is executor


def test_registry_supports_multiple_capabilities():
    live_executor = FakeLiveIntelligenceExecutor()
    podcast_executor = FakePodcastDiscoveryExecutor()
    evaluation_executor = FakeEvaluationExecutor()

    registry = CapabilityRegistry(
        executors=[
            live_executor,
            podcast_executor,
            evaluation_executor,
        ]
    )

    assert (
        registry.resolve(
            CapabilityType.LIVE_INTELLIGENCE
        )
        is live_executor
    )

    assert (
        registry.resolve(
            CapabilityType.PODCAST_DISCOVERY
        )
        is podcast_executor
    )

    assert (
        registry.resolve(
            CapabilityType.EVALUATION
        )
        is evaluation_executor
    )


def test_registry_supports_learning_generation_capability():
    live_executor = FakeLiveIntelligenceExecutor()
    podcast_executor = FakePodcastDiscoveryExecutor()
    evaluation_executor = FakeEvaluationExecutor()
    learning_executor = (
        PodcastLearningChallengeExecutor()
    )

    registry = CapabilityRegistry(
        executors=[
            live_executor,
            podcast_executor,
            evaluation_executor,
            learning_executor,
        ]
    )

    assert (
        registry.resolve(
            CapabilityType.LIVE_INTELLIGENCE
        )
        is live_executor
    )

    assert (
        registry.resolve(
            CapabilityType.PODCAST_DISCOVERY
        )
        is podcast_executor
    )

    assert (
        registry.resolve(
            CapabilityType.EVALUATION
        )
        is evaluation_executor
    )

    assert (
        registry.resolve(
            CapabilityType.LEARNING_GENERATION
        )
        is learning_executor
    )


def test_duplicate_capability_registration_is_rejected():
    registry = CapabilityRegistry()

    registry.register(
        FakeLiveIntelligenceExecutor()
    )

    with pytest.raises(
        CapabilityAlreadyRegisteredError,
        match="already registered",
    ):
        registry.register(
            FakeLiveIntelligenceExecutor()
        )


def test_duplicate_podcast_capability_registration_is_rejected():
    registry = CapabilityRegistry()

    registry.register(
        FakePodcastDiscoveryExecutor()
    )

    with pytest.raises(
        CapabilityAlreadyRegisteredError,
        match="already registered",
    ):
        registry.register(
            FakePodcastDiscoveryExecutor()
        )


def test_duplicate_learning_generation_registration_is_rejected():
    registry = CapabilityRegistry()

    registry.register(
        PodcastLearningChallengeExecutor()
    )

    with pytest.raises(
        CapabilityAlreadyRegisteredError,
        match="already registered",
    ):
        registry.register(
            PodcastLearningChallengeExecutor()
        )


def test_unknown_capability_resolution_is_rejected():
    registry = CapabilityRegistry()

    with pytest.raises(
        CapabilityNotRegisteredError,
        match="No executor registered",
    ):
        registry.resolve(
            CapabilityType.LEARNING_GENERATION
        )


def test_contains_returns_false_for_unknown_capability():
    registry = CapabilityRegistry()

    assert (
        registry.contains(
            CapabilityType.EVALUATION
        )
        is False
    )

    assert (
        registry.contains(
            CapabilityType.PODCAST_DISCOVERY
        )
        is False
    )

    assert (
        registry.contains(
            CapabilityType.LEARNING_GENERATION
        )
        is False
    )


def test_capabilities_returns_registered_capabilities():
    registry = CapabilityRegistry(
        executors=[
            FakeLiveIntelligenceExecutor(),
            FakePodcastDiscoveryExecutor(),
            FakeEvaluationExecutor(),
        ]
    )

    capabilities = registry.capabilities()

    assert (
        CapabilityType.LIVE_INTELLIGENCE
        in capabilities
    )

    assert (
        CapabilityType.PODCAST_DISCOVERY
        in capabilities
    )

    assert (
        CapabilityType.EVALUATION
        in capabilities
    )

    assert (
        CapabilityType.LEARNING_GENERATION
        not in capabilities
    )


def test_capabilities_includes_learning_generation():
    registry = CapabilityRegistry(
        executors=[
            FakeLiveIntelligenceExecutor(),
            FakePodcastDiscoveryExecutor(),
            FakeEvaluationExecutor(),
            PodcastLearningChallengeExecutor(),
        ]
    )

    capabilities = registry.capabilities()

    assert (
        CapabilityType.LIVE_INTELLIGENCE
        in capabilities
    )

    assert (
        CapabilityType.PODCAST_DISCOVERY
        in capabilities
    )

    assert (
        CapabilityType.EVALUATION
        in capabilities
    )

    assert (
        CapabilityType.LEARNING_GENERATION
        in capabilities
    )