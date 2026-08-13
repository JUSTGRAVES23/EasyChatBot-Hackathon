"""
AI Runtime executor for Live Intelligence.

This adapter bridges the provider-independent AI Runtime
capability contract with the existing LiveIntelligenceAgent.

Architecture:

AI Runtime
    |
    v
CapabilityRequest
    |
    v
LiveIntelligenceExecutor
    |
    v
LiveIntelligenceAgent
    |
    v
LiveIntelligenceResponse

The adapter:

- validates the Runtime capability;
- translates Runtime payloads into LiveIntelligenceRequest;
- invokes the existing Live Intelligence Agent;
- translates the agent response into CapabilityResult.

It does not:

- implement intelligence logic;
- call providers directly;
- modify the LiveIntelligenceAgent;
- perform governance decisions.
"""

from __future__ import annotations

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
    LiveIntelligenceRequest,
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


class LiveIntelligenceExecutor(
    CapabilityExecutor,
):
    """
    Runtime adapter for the existing LiveIntelligenceAgent.
    """

    def __init__(
        self,
        agent: LiveIntelligenceAgent,
    ) -> None:
        """
        Create Runtime executor.

        Agent dependency is injected from composition.
        """

        if agent is None:
            raise ValueError(
                "LiveIntelligenceAgent cannot be None."
            )

        self._agent = agent

    @property
    def capability(
        self,
    ) -> CapabilityType:
        """
        Return the capability handled by this executor.
        """

        return CapabilityType.LIVE_INTELLIGENCE

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        """
        Translate and execute a Live Intelligence request.
        """

        if request is None:
            raise ValueError(
                "CapabilityRequest cannot be None."
            )

        if (
            request.capability
            != CapabilityType.LIVE_INTELLIGENCE
        ):
            raise ValueError(
                "LiveIntelligenceExecutor received "
                "an unsupported capability: "
                f"{request.capability.value}"
            )

        agent_request = (
            self._build_agent_request(
                request,
            )
        )

        response = await self._agent.execute(
            agent_request,
        )

        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            status=(
                CapabilityExecutionStatus.COMPLETED
            ),
            output=response,
            metadata={
                "executor": (
                    "live_intelligence_executor"
                ),
            },
        )

    @staticmethod
    def _build_agent_request(
        request: CapabilityRequest,
    ) -> LiveIntelligenceRequest:
        """
        Translate Runtime payload into the existing
        LiveIntelligenceRequest contract.
        """

        payload = request.payload

        topic = payload.get(
            "topic",
        )

        if not isinstance(
            topic,
            str,
        ):
            raise ValueError(
                "Live Intelligence capability requires "
                "a string 'topic'."
            )

        if not topic.strip():
            raise ValueError(
                "Live Intelligence 'topic' cannot "
                "be empty."
            )

        language = payload.get(
            "language",
            "French",
        )

        learner_level = payload.get(
            "learner_level",
            "B2",
        )

        if not isinstance(
            language,
            str,
        ):
            raise ValueError(
                "Live Intelligence 'language' "
                "must be a string."
            )

        if not isinstance(
            learner_level,
            str,
        ):
            raise ValueError(
                "Live Intelligence 'learner_level' "
                "must be a string."
            )

        return LiveIntelligenceRequest(
            topic=topic,
            language=language,
            learner_level=learner_level,
        )