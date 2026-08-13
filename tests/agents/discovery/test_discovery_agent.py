"""
Tests for the EasyChatBot Discovery Agent.

These tests verify the Beta 1 vertical slice:

PreferenceSource
    ↓
PreferenceContext
    ↓
PreferenceUnderstandingSkill
    ↓
DiscoveryProfile
    ↓
DiscoveryAgent
"""

from __future__ import annotations

import pytest

from backend.agents.discovery.discovery_agent import (
    DiscoveryAgent,
)
from backend.runtime.context.execution_context import (
    ExecutionContext,
)
from backend.skills.discovery.hackathon_preference_source import (
    HackathonPreferenceSource,
)
from backend.skills.discovery.preference_source import (
    PreferenceContext,
)
from backend.skills.discovery.preference_understanding import (
    PreferenceUnderstandingSkill,
)


@pytest.mark.asyncio
async def test_discovery_agent_uses_onboarding_preferences():
    """
    DiscoveryAgent should obtain approved onboarding preferences
    through PreferenceSource and expose them in the resulting profile.
    """

    source = HackathonPreferenceSource(
        {
            "topics": [
                "artificial intelligence",
                "technology",
            ],
            "content_types": [
                "podcasts",
                "news",
            ],
            "languages": [
                "french",
            ],
            "learning_level": "B2",
        }
    )

    agent = DiscoveryAgent(
        preference_source=source,
    )

    context = ExecutionContext(
        user_id="discovery-test-user",
        request="Find me something about artificial intelligence.",
    )

    result = await agent.execute(context)

    assert result.success is True
    assert result.agent_id == "discovery_agent"

    profile = result.output["discovery_profile"]

    assert "artificial intelligence" in profile["topics"]
    assert "technology" in profile["topics"]

    assert "podcast" in profile["content_types"]
    assert "news" in profile["content_types"]

    assert "french" in profile["languages"]
    assert profile["learning_level"] == "B2"


@pytest.mark.asyncio
async def test_current_request_has_precedence_over_onboarding_context():
    """
    Explicit content preferences in the current request should be
    placed before onboarding defaults.
    """

    source = HackathonPreferenceSource(
        {
            "content_types": [
                "news",
            ],
            "languages": [
                "french",
            ],
        }
    )

    agent = DiscoveryAgent(
        preference_source=source,
    )

    context = ExecutionContext(
        user_id="discovery-test-user",
        request="Find podcasts about artificial intelligence.",
    )

    result = await agent.execute(context)

    assert result.success is True

    profile = result.output["discovery_profile"]

    assert profile["content_types"][0] == "podcast"
    assert "news" in profile["content_types"]

    assert "artificial intelligence" in profile["topics"]


@pytest.mark.asyncio
async def test_discovery_agent_works_without_onboarding_preferences():
    """
    The hackathon Discovery Agent must remain functional when no
    onboarding preferences are available.
    """

    source = HackathonPreferenceSource()

    agent = DiscoveryAgent(
        preference_source=source,
    )

    context = ExecutionContext(
        user_id="discovery-test-user",
        request="Find podcasts about artificial intelligence.",
    )

    result = await agent.execute(context)

    assert result.success is True

    profile = result.output["discovery_profile"]

    assert "artificial intelligence" in profile["topics"]
    assert "podcast" in profile["content_types"]


@pytest.mark.asyncio
async def test_discovery_agent_rejects_empty_request():
    """
    Empty discovery requests should fail before Skill execution.
    """

    agent = DiscoveryAgent(
        preference_source=HackathonPreferenceSource()
    )

    context = ExecutionContext(
        user_id="discovery-test-user",
        request="   ",
    )

    result = await agent.execute(context)

    assert result.success is False
    assert (
        result.error
        == "Execution context request cannot be empty."
    )


@pytest.mark.asyncio
async def test_preference_skill_accepts_preference_context():
    """
    PreferenceUnderstandingSkill should consume PreferenceContext
    through generic SkillInput metadata.
    """

    from backend.skills.skill import SkillInput

    skill = PreferenceUnderstandingSkill()

    preference_context = PreferenceContext(
        topics=(
            "artificial intelligence",
        ),
        content_types=(
            "podcast",
        ),
        languages=(
            "french",
        ),
        learning_level="B2",
        source="onboarding",
    )

    result = await skill.execute(
        SkillInput(
            request="Find something about AI.",
            user_id="discovery-test-user",
            metadata={
                "preference_context": preference_context,
            },
        )
    )

    assert result.success is True

    profile = result.output

    assert (
        "artificial intelligence"
        in profile.topics
    )

    assert "podcast" in profile.content_types
    assert "french" in profile.languages
    assert profile.learning_level == "B2"