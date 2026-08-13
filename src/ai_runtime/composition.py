"""
External AI Runtime composition.

This module is the composition root for the external/user-assistance
AI Runtime used by EasyChatBot.

The composition root wires together:

Governance
    |
    v
CapabilityGateway
    |
    v
CapabilityRegistry
    |
    +--> Live Intelligence
    +--> Podcast Discovery
    +--> Learning Generation
    +--> Podcast Listening Proposal
    +--> Flashcard Generation


Responsibilities:

- dependency injection;
- Runtime component composition;
- capability registration.

This module does not:

- implement capability business logic;
- implement provider logic;
- retrieve learner memory;
- make governance decisions;
- execute agents directly;
- perform external side effects;
- modify the internal AI Agents framework.

The internal AI Agents framework remains a separate system.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
)

from src.ai_runtime.capabilities.executor import (
    CapabilityExecutor,
)

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_runtime.capabilities.listening_proposal_executor import (
    ListeningProposalExecutor,
)

from src.ai_runtime.capabilities.live_intelligence_executor import (
    LiveIntelligenceExecutor,
)

from src.ai_runtime.capabilities.podcast_discovery_executor import (
    PodcastDiscoveryExecutor,
)

from src.ai_runtime.capabilities.podcast_learning_challenge_executor import (
    PodcastLearningChallengeExecutor,
)

from src.ai_runtime.capabilities.flashcard_generation_executor import (
    FlashcardGenerationExecutor,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)

from src.ai_runtime.podcast.agent import (
    PodcastDiscoveryAgent,
)

from src.ai_runtime.podcast.providers import (
    PodcastProvider,
)


def create_capability_executors(
    *,
    live_intelligence_agent: LiveIntelligenceAgent,
    podcast_discovery_agent: PodcastDiscoveryAgent,
    podcast_providers: Sequence[PodcastProvider],
) -> tuple[CapabilityExecutor, ...]:
    """
    Create Runtime capability executors.

    Dependencies are injected from the composition layer.

    This function does not:

    - create providers;
    - create agents;
    - access external systems;
    - retrieve learner data.
    """

    if live_intelligence_agent is None:
        raise ValueError(
            "LiveIntelligenceAgent cannot be None."
        )

    if podcast_discovery_agent is None:
        raise ValueError(
            "PodcastDiscoveryAgent cannot be None."
        )

    if not podcast_providers:
        raise ValueError(
            "At least one PodcastProvider is required."
        )

    return (
        LiveIntelligenceExecutor(
            agent=live_intelligence_agent,
        ),

        PodcastDiscoveryExecutor(
            agent=podcast_discovery_agent,
            providers=podcast_providers,
        ),

        PodcastLearningChallengeExecutor(),

        ListeningProposalExecutor(),

        FlashcardGenerationExecutor(),
    )


def create_capability_registry(
    *,
    live_intelligence_agent: LiveIntelligenceAgent,
    podcast_discovery_agent: PodcastDiscoveryAgent,
    podcast_providers: Sequence[PodcastProvider],
) -> CapabilityRegistry:
    """
    Create Runtime capability registry.

    Registry owns capability lookup only.

    It does not:

    - execute governance;
    - select providers;
    - manage application state.
    """

    executors = create_capability_executors(
        live_intelligence_agent=(
            live_intelligence_agent
        ),
        podcast_discovery_agent=(
            podcast_discovery_agent
        ),
        podcast_providers=(
            podcast_providers
        ),
    )

    return CapabilityRegistry(
        executors=list(executors),
    )


def create_capability_gateway(
    *,
    registry: CapabilityRegistry,
    governance: Any,
) -> CapabilityGateway:
    """
    Create Runtime gateway.

    Governance is injected.

    Gateway responsibilities:

    - capability access control;
    - governance enforcement;
    - execution delegation.
    """

    if registry is None:
        raise ValueError(
            "CapabilityRegistry cannot be None."
        )

    if governance is None:
        raise ValueError(
            "Governance cannot be None."
        )

    return CapabilityGateway(
        registry=registry,
        governance=governance,
    )


def create_external_runtime_gateway(
    *,
    live_intelligence_agent: LiveIntelligenceAgent,
    podcast_discovery_agent: PodcastDiscoveryAgent,
    podcast_providers: Sequence[PodcastProvider],
    governance: Any,
) -> CapabilityGateway:
    """
    Main Runtime composition entry point.

    Flow:

        Dependencies
             |
             v
        Executors
             |
             v
        Registry
             |
             v
        Gateway
             |
             v
        Application Service

    Returns:

        Configured CapabilityGateway.
    """

    if live_intelligence_agent is None:
        raise ValueError(
            "LiveIntelligenceAgent cannot be None."
        )

    if podcast_discovery_agent is None:
        raise ValueError(
            "PodcastDiscoveryAgent cannot be None."
        )

    if not podcast_providers:
        raise ValueError(
            "At least one PodcastProvider is required."
        )

    if governance is None:
        raise ValueError(
            "Governance cannot be None."
        )

    registry = create_capability_registry(
        live_intelligence_agent=(
            live_intelligence_agent
        ),
        podcast_discovery_agent=(
            podcast_discovery_agent
        ),
        podcast_providers=(
            podcast_providers
        ),
    )

    return create_capability_gateway(
        registry=registry,
        governance=governance,
    )