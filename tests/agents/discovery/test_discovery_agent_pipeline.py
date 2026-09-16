"""
End-to-end Discovery Agent pipeline tests.

Defines the intended Beta 1 vertical slice:
Preference Understanding -> Query Generation -> Discovery ->
Relevance Matching -> Ranking -> Explanation -> Personalisation ->
Quality Verification -> User Choice / Controlled Handoff.

Uses an in-memory DiscoveryGateway so the tests do not require
external provider credentials.
"""

from __future__ import annotations

import pytest

from agents.discovery.discovery_agent import DiscoveryAgent
from runtime.context.execution_context import ExecutionContext

from skills.discovery.content_product_discovery import (
    ContentProductDiscoverySkill,
    DiscoveryCandidate,
)
from skills.discovery.discovery_quality_verification import (
    DiscoveryQualityVerificationSkill,
)
from skills.discovery.hackathon_preference_source import (
    HackathonPreferenceSource,
)
from skills.discovery.personalised_content_adaptation import (
    PersonalisedContentAdaptationSkill,
)
from skills.discovery.preference_understanding import (
    PreferenceUnderstandingSkill,
)
from skills.discovery.query_generation import (
    DiscoveryQuery,
    DiscoveryQueryGenerationSkill,
)
from skills.discovery.recommendation_explanation import (
    RecommendationExplanationSkill,
)
from skills.discovery.recommendation_ranking import (
    RecommendationRankingSkill,
)
from skills.discovery.relevance_matching import (
    RelevanceMatchingSkill,
)
from skills.discovery.user_choice_handoff import (
    UserChoiceControlledHandoffSkill,
)


class FakeDiscoveryGateway:
    """Deterministic in-memory DiscoveryGateway for integration tests."""

    def __init__(self) -> None:
        self.queries: list[DiscoveryQuery] = []

    async def discover(
        self,
        query: DiscoveryQuery,
    ) -> list[DiscoveryCandidate]:
        self.queries.append(query)

        if query.content_type == "podcast":
            return [
                DiscoveryCandidate(
                    title="Artificial Intelligence Podcast",
                    url="https://example.com/ai-podcast",
                    description=(
                        "A beginner friendly French podcast "
                        "about artificial intelligence and technology."
                    ),
                    content_type="podcast",
                    source="fake",
                    metadata={"language": "french"},
                )
            ]

        if query.content_type == "news":
            return [
                DiscoveryCandidate(
                    title="AI Technology News",
                    url="https://example.com/ai-news",
                    description=(
                        "French news covering artificial "
                        "intelligence and technology."
                    ),
                    content_type="news",
                    source="fake",
                    metadata={"language": "french"},
                )
            ]

        return []


def build_discovery_agent(
    gateway: FakeDiscoveryGateway,
) -> DiscoveryAgent:
    """Build the complete Discovery Agent with nine injected Skills."""

    return DiscoveryAgent(
        preference_skill=PreferenceUnderstandingSkill(),
        preference_source=HackathonPreferenceSource(
            {
                "topics": (
                    "artificial intelligence",
                    "technology",
                ),
                "content_types": (
                    "podcasts",
                    "news",
                ),
                "languages": ("french",),
                "learning_level": "B2",
            }
        ),
        query_generation_skill=DiscoveryQueryGenerationSkill(),
        discovery_skill=ContentProductDiscoverySkill(
            gateway=gateway,
        ),
        relevance_matching_skill=RelevanceMatchingSkill(),
        recommendation_ranking_skill=RecommendationRankingSkill(),
        recommendation_explanation_skill=(
            RecommendationExplanationSkill()
        ),
        personalised_content_adaptation_skill=(
            PersonalisedContentAdaptationSkill()
        ),
        quality_verification_skill=(
            DiscoveryQualityVerificationSkill()
        ),
        user_choice_handoff_skill=(
            UserChoiceControlledHandoffSkill()
        ),
    )


@pytest.mark.asyncio
async def test_full_discovery_pipeline_reaches_user_choice_boundary():
    """The complete pipeline must stop at explicit user choice."""

    gateway = FakeDiscoveryGateway()
    agent = build_discovery_agent(gateway)

    context = ExecutionContext(
        user_id="pipeline-test-user",
        request=(
            "Find me a French podcast about artificial "
            "intelligence and technology."
        ),
    )

    result = await agent.execute(context)

    assert result.success is True
    assert result.agent_id == "discovery_agent"

    output = result.output

    assert output["discovery_profile"]["content_types"] == [
        "podcast",
        "news",
    ]
    assert "artificial intelligence" in (
        output["discovery_profile"]["topics"]
    )

    assert output["skills_executed"] == [
        "discovery.preference_understanding",
        "discovery.query_generation",
        "discovery.content_product_discovery",
        "discovery.relevance_matching",
        "discovery.recommendation_ranking",
        "discovery.recommendation_explanation",
        "discovery.personalised_content_adaptation",
        "discovery.quality_verification",
        "discovery.user_choice_handoff",
    ]

    assert output["status"] == "awaiting_user_choice"
    assert output["handoff"] is None
    assert output["options"]
    assert len(gateway.queries) == 2


@pytest.mark.asyncio
async def test_discovery_pipeline_requires_explicit_user_choice():
    """A valid explicit selection should create a controlled handoff."""

    gateway = FakeDiscoveryGateway()
    agent = build_discovery_agent(gateway)

    context = ExecutionContext(
        user_id="pipeline-choice-user",
        request="Find me a French podcast about artificial intelligence.",
        metadata={
            "selected_option_id": "recommendation-1",
        },
    )

    result = await agent.execute(context)

    assert result.success is True
    assert result.agent_id == "discovery_agent"

    output = result.output

    assert output["status"] == "handoff_approved"

    handoff = output["handoff"]

    assert handoff is not None
    assert handoff.option_id == "recommendation-1"
    assert handoff.rank == 1
    assert (
        handoff.recommendation
        .recommendation
        .recommendation
        .candidate
        .url
        == "https://example.com/ai-podcast"
    )


@pytest.mark.asyncio
async def test_discovery_pipeline_does_not_bypass_gateway():
    """External discovery remains behind the DiscoveryGateway boundary."""

    gateway = FakeDiscoveryGateway()
    agent = build_discovery_agent(gateway)

    context = ExecutionContext(
        user_id="gateway-test-user",
        request="Find French AI podcasts.",
    )

    result = await agent.execute(context)

    assert result.success is True
    assert gateway.queries

    assert all(
        isinstance(query, DiscoveryQuery)
        for query in gateway.queries
    )

