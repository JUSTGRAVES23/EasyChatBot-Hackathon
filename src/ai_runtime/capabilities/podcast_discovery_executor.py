"""
AI Runtime executor for Podcast Discovery.

This adapter bridges the provider-independent AI Runtime capability
contract with the existing Podcast Discovery Agent and
Podcast Recommendation Service.

Architecture:

AI Runtime
    |
    v
CapabilityRequest
    |
    v
PodcastDiscoveryExecutor
    |
    +--> PodcastDiscoveryAgent
    |
    +--> PodcastRecommendationService
    |
    v
PodcastRecommendation
    |
    v
CapabilityResult

The executor:

- validates the Runtime capability;
- validates explicit capability inputs;
- builds the existing LearningContext;
- passes explicit learner memories to the PodcastDiscoveryAgent;
- invokes the existing PodcastRecommendationService;
- returns a provider-independent CapabilityResult.

It does not:

- call Apple directly;
- call Spotify directly;
- implement provider logic;
- retrieve memory itself;
- modify MemoryService;
- perform purchases;
- bypass the AI Runtime;
- make governance decisions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.ai_runtime.capabilities.executor import (
    CapabilityExecutor,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityResult,
    CapabilityType,
)

from src.ai_runtime.memory.models import (
    MemoryEntry,
)

from src.ai_runtime.podcast.agent import (
    PodcastDiscoveryAgent,
)

from src.ai_runtime.podcast.models import (
    LearningContext,
)

from src.ai_runtime.podcast.providers import (
    PodcastProvider,
)

from src.ai_runtime.podcast.service import (
    PodcastRecommendationService,
)


class PodcastDiscoveryExecutor(
    CapabilityExecutor,
):
    """
    Runtime adapter for the existing Podcast Discovery flow.
    """

    def __init__(
        self,
        agent: PodcastDiscoveryAgent,
        providers: Sequence[PodcastProvider],
    ) -> None:
        """
        Create Podcast Discovery executor.

        Dependencies are injected from Runtime composition.
        """

        if agent is None:
            raise ValueError(
                "PodcastDiscoveryAgent cannot be None."
            )

        if not providers:
            raise ValueError(
                "PodcastDiscoveryExecutor requires "
                "at least one provider."
            )

        self._agent = agent

        self._recommendation_service = (
            PodcastRecommendationService(
                providers=list(providers),
            )
        )

    @property
    def capability(
        self,
    ) -> CapabilityType:
        """
        Return the capability handled by this executor.
        """

        return CapabilityType.PODCAST_DISCOVERY

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        """
        Execute a provider-independent podcast discovery request.
        """

        if request is None:
            raise ValueError(
                "CapabilityRequest cannot be None."
            )

        if (
            request.capability
            != CapabilityType.PODCAST_DISCOVERY
        ):
            raise ValueError(
                "PodcastDiscoveryExecutor received "
                "an unsupported capability: "
                f"{request.capability.value}"
            )

        intent = self._build_search_intent(
            request,
        )

        recommendation = (
            self._recommendation_service.recommend(
                intent=intent,
                character_id=self._required_string(
                    request.payload,
                    "character_id",
                ),
                character_name=self._required_string(
                    request.payload,
                    "character_name",
                ),
                character_message=self._required_string(
                    request.payload,
                    "character_message",
                ),
            )
        )

        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            status=(
                CapabilityExecutionStatus.COMPLETED
            ),
            output=recommendation,
            metadata={
                "executor": (
                    "podcast_discovery_executor"
                ),
            },
        )

    def _build_search_intent(
        self,
        request: CapabilityRequest,
    ):
        """
        Translate Runtime payload into the existing
        PodcastSearchIntent through PodcastDiscoveryAgent.
        """

        payload = request.payload

        user_id = self._required_string(
            payload,
            "user_id",
        )

        learning_context = (
            self._build_learning_context(
                payload,
            )
        )

        memories = self._build_memories(
            payload,
        )

        max_results = payload.get(
            "max_results",
            10,
        )

        if not isinstance(
            max_results,
            int,
        ):
            raise ValueError(
                "Podcast Discovery 'max_results' "
                "must be an integer."
            )

        if max_results < 1:
            raise ValueError(
                "Podcast Discovery 'max_results' "
                "must be at least 1."
            )

        return self._agent.build_search_intent(
            user_id=user_id,
            learning_context=learning_context,
            memories=memories,
            max_results=max_results,
        )

    @staticmethod
    def _build_learning_context(
        payload: Mapping[str, Any],
    ) -> LearningContext:
        """
        Build provider-independent LearningContext.
        """

        world_id = payload.get(
            "world_id",
            "French World",
        )

        target_language = payload.get(
            "target_language",
            "fr",
        )

        learner_level = payload.get(
            "learner_level",
            "B2",
        )

        learning_goal = payload.get(
            "learning_goal",
            "",
        )

        country_code = payload.get(
            "country_code",
            "LU",
        )

        preferred_languages = payload.get(
            "preferred_languages",
            (),
        )

        values = {
            "world_id": world_id,
            "target_language": target_language,
            "learner_level": learner_level,
            "learning_goal": learning_goal,
            "country_code": country_code,
        }

        for name, value in values.items():
            if not isinstance(
                value,
                str,
            ):
                raise ValueError(
                    f"Podcast Discovery '{name}' "
                    "must be a string."
                )

        if not isinstance(
            preferred_languages,
            (list, tuple),
        ):
            raise ValueError(
                "Podcast Discovery "
                "'preferred_languages' "
                "must be a list or tuple."
            )

        if not all(
            isinstance(language, str)
            for language in preferred_languages
        ):
            raise ValueError(
                "Podcast Discovery "
                "'preferred_languages' "
                "must contain only strings."
            )

        return LearningContext(
            world_id=world_id,
            target_language=target_language,
            learner_level=learner_level,
            learning_goal=learning_goal,
            preferred_languages=tuple(
                preferred_languages
            ),
            country_code=country_code,
        )

    @staticmethod
    def _build_memories(
        payload: Mapping[str, Any],
    ) -> list[MemoryEntry]:
        """
        Validate explicit learner memories.

        Memory retrieval remains outside this executor.
        """

        memories = payload.get(
            "memories",
            (),
        )

        if not isinstance(
            memories,
            (list, tuple),
        ):
            raise ValueError(
                "Podcast Discovery 'memories' "
                "must be a list or tuple."
            )

        for memory in memories:
            if not isinstance(
                memory,
                MemoryEntry,
            ):
                raise ValueError(
                    "Podcast Discovery 'memories' "
                    "must contain only "
                    "MemoryEntry objects."
                )

        return list(memories)

    @staticmethod
    def _required_string(
        payload: Mapping[str, Any],
        field_name: str,
    ) -> str:
        """
        Return a required non-empty string payload value.
        """

        value = payload.get(
            field_name,
        )

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                f"Podcast Discovery '{field_name}' "
                "must be a string."
            )

        if not value.strip():
            raise ValueError(
                f"Podcast Discovery '{field_name}' "
                "cannot be empty."
            )

        return value