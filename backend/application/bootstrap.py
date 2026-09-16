from __future__ import annotations

from collections.abc import Sequence

from app.domain.authorization.permissions import (
    Permission,
    has_permission,
)
from application.factory import (
    ApplicationFactory,
)
from application.internal_documentation_composition import (
    create_internal_documentation_agent_from_repository,
)
from runtime.external_runtime_container import (
    configure_external_runtime_service,
    get_external_runtime_service as _get_external_runtime_service,
)
from services.external_runtime_service import (
    ExternalRuntimeService,
)
from src.ai_runtime.composition import (
    create_external_runtime_gateway,
)
from src.ai_agents.live_intelligence_agent.composition import (
    create_live_intelligence_agent,
)
from src.ai_runtime.podcast.parallel import (
    ParallelPodcastProvider,
)
from src.ai_runtime.capabilities.actor_context import RuntimeActorContext


_bootstrapped = False


def bootstrap_application() -> None:
    """
    Bootstrap application dependencies.

    Creates the ExternalRuntimeService and registers it
    inside the application runtime container.
    """

    global _bootstrapped

    if _bootstrapped:
        return

    factory = ApplicationFactory()

    gateway = create_external_runtime_gateway(
        live_intelligence_agent=(
            create_live_intelligence_agent()
        ),
        podcast_discovery_agent=(
            create_podcast_discovery_agent()
        ),
        podcast_providers=(
            create_podcast_providers()
        ),
        governance=(
            create_governance()
        ),
        internal_documentation_agent=(
            create_internal_documentation_agent_from_repository()
        ),
    )

    runtime_service = (
        factory.create_external_runtime_service(
            gateway=gateway,
        )
    )

    configure_external_runtime_service(
        runtime_service,
    )

    _bootstrapped = True


def get_external_runtime_service() -> ExternalRuntimeService:
    """
    Backward-compatible Runtime accessor.
    """

    return _get_external_runtime_service()


def reset_bootstrap() -> None:
    """
    Test-only reset.
    """

    global _bootstrapped

    _bootstrapped = False


# =========================================================
# Podcast Runtime Dependencies
# =========================================================


class BootstrapPlaceholderPodcastAgent:
    """
    Temporary Podcast Discovery Agent adapter.

    Kept only for hackathon compatibility.
    """

    def build_search_intent(
        self,
        *,
        user_id: str,
        learning_context,
        memories,
        max_results: int,
    ):
        from src.ai_runtime.podcast.models import (
            PodcastSearchIntent,
        )

        return PodcastSearchIntent(
            user_id=user_id,
            learning_context=learning_context,
            topics=(
                "French learning podcast",
            ),
            keywords=(
                "French",
                "learning",
                "listening",
            ),
            max_results=max_results,
        )


def create_podcast_discovery_agent():
    """
    Create Podcast Discovery Agent.
    """

    return BootstrapPlaceholderPodcastAgent()


def create_podcast_providers() -> Sequence:
    """
    Create Podcast provider collection.
    """

    return [
        ParallelPodcastProvider(
            client=BootstrapParallelClient(),
        ),
    ]


class BootstrapParallelClient:
    """
    Deterministic hackathon Parallel client.

    Not the provider.

    Represents the external provider boundary.
    """

    def search(
        self,
        intent,
    ) -> list[dict[str, object]]:

        return [
            {
                "id": (
                    "demo-french-podcast-001"
                ),
                "title": (
                    "French Learning Podcast"
                ),
                "description": (
                    "French listening practice "
                    "for B2 learners."
                ),
                "publisher": (
                    "EasyChatBot Demo"
                ),
                "languages": [
                    "fr",
                ],
                "url": (
                    "https://example.com/"
                    "french-learning-podcast"
                ),
            }
        ]


# =========================================================
# Governance
# =========================================================


class BootstrapGovernanceDecision:
    """
    Runtime governance decision.
    """

    def __init__(
        self,
        allowed: bool,
    ) -> None:

        self.allowed = allowed


class BootstrapGovernance:
    """
    Temporary hackathon governance implementation.

    Sensitive internal-data capabilities fail closed.

    The Runtime receives a provider-independent
    RuntimeActorContext. Application/API identity remains
    outside the Runtime boundary.
    """

    def evaluate(
        self,
        request,
    ) -> BootstrapGovernanceDecision:

        capability = getattr(
            request,
            "capability",
            None,
        )

        capability_value = getattr(
            capability,
            "value",
            capability,
        )

        if capability_value == "internal_data_read":
            actor = getattr(
                request,
                "actor",
                None,
            )

            if not isinstance(
                actor,
                RuntimeActorContext,
            ):
                return BootstrapGovernanceDecision(
                    allowed=False,
                )

            allowed = has_permission(
                roles=actor.roles,
                permission=Permission.INTERNAL_DATA_READ,
            )

            return BootstrapGovernanceDecision(
                allowed=allowed,
            )

        return BootstrapGovernanceDecision(
            allowed=True,
        )


def create_governance():
    """
    Create Runtime governance dependency.
    """

    return BootstrapGovernance()

