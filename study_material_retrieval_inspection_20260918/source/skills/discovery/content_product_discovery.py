"""
Content/Product Discovery Skill.

Executes provider-independent discovery queries through an injected
Discovery Gateway.

The Skill converts discovery intent into normalized discovery
candidates.

It does not:

- call provider SDKs directly
- select providers
- manage memory
- modify learner preferences
- rank recommendations
- decide final recommendations
- perform uncontrolled external actions

Provider selection and external communication remain outside the Skill.

Architecture:

DiscoveryQueryGenerationSkill
            |
            v
ContentProductDiscoverySkill
            |
            v
DiscoveryGateway
            |
            v
Approved Provider
            |
            v
DiscoveryCandidate[]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from skills.discovery.query_generation import (
    DiscoveryQuery,
)
from skills.skill import (
    Skill,
    SkillInput,
)
from skills.skill_result import (
    SkillResult,
)


@dataclass(frozen=True)
class DiscoveryCandidate:
    """
    Normalized provider-independent discovery candidate.

    The candidate represents an item discovered from an external
    source without exposing provider-specific response structures
    to downstream Skills.

    Attributes
    ----------
    title:
        Human-readable candidate title.

    url:
        Canonical candidate URL.

    description:
        Short candidate description or excerpt.

    content_type:
        Canonical discovery type.

    source:
        Provider or source identifier.

    metadata:
        Additional provider-neutral metadata.
    """

    title: str
    url: str
    description: str = ""
    content_type: str = "article"
    source: str = "unknown"
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def as_dict(self) -> dict[str, Any]:
        """Return a serialisable representation."""

        return {
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "content_type": self.content_type,
            "source": self.source,
            "metadata": dict(self.metadata),
        }


class DiscoveryGateway(Protocol):
    """
    Provider-independent Discovery Gateway contract.

    Implementations belong to the infrastructure/provider boundary.

    The Skill knows only that the gateway can execute a
    DiscoveryQuery and return provider-independent candidates.

    The gateway must not:

    - modify learner memory
    - modify learner preferences
    - perform uncontrolled actions
    """

    async def discover(
        self,
        query: DiscoveryQuery,
    ) -> list[DiscoveryCandidate]:
        """Discover candidates for the supplied query."""
        ...


class ContentProductDiscoverySkill(Skill):
    """
    Discover podcasts, news, articles and products.

    The Skill delegates external discovery to an injected
    DiscoveryGateway.

    This keeps the Skill independent from Parallel, Spotify,
    YouTube, news providers, commerce providers, or future
    discovery services.
    """

    skill_id = (
        "discovery.content_product_discovery"
    )

    name = "Content/Product Discovery"

    version = "1.0.0"

    _MAX_CANDIDATES = 20

    def __init__(
        self,
        gateway: DiscoveryGateway,
    ) -> None:
        """
        Initialise the Skill.

        Parameters
        ----------
        gateway:
            Provider-independent discovery gateway.
        """

        if gateway is None:
            raise ValueError(
                "Discovery gateway is required."
            )

        self.gateway = gateway

    async def execute(
        self,
        skill_input: SkillInput,
    ) -> SkillResult:
        """
        Execute discovery for previously generated queries.

        Expected metadata:

            {
                "discovery_queries": (
                    DiscoveryQuery(...)
                )
            }

        Query generation remains the responsibility of
        DiscoveryQueryGenerationSkill.
        """

        if skill_input is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="Skill input cannot be None.",
            )

        raw_queries = skill_input.metadata.get(
            "discovery_queries"
        )

        if raw_queries is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="discovery_queries are required.",
            )

        if not isinstance(
            raw_queries,
            (list, tuple),
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "discovery_queries must be a "
                    "list or tuple of DiscoveryQuery."
                ),
            )

        queries: list[DiscoveryQuery] = []

        for query in raw_queries:
            if not isinstance(
                query,
                DiscoveryQuery,
            ):
                return SkillResult.failed(
                    skill_id=self.skill_id,
                    error=(
                        "All discovery_queries must "
                        "be DiscoveryQuery instances."
                    ),
                )

            queries.append(query)

        if not queries:
            return SkillResult.succeeded(
                skill_id=self.skill_id,
                output=[],
            )

        candidates: list[DiscoveryCandidate] = []

        for query in queries:
            discovered = await self.gateway.discover(
                query
            )

            if not discovered:
                continue

            for candidate in discovered:

                if not isinstance(
                    candidate,
                    DiscoveryCandidate,
                ):
                    continue

                if not candidate.title.strip():
                    continue

                if not candidate.url.strip():
                    continue

                candidates.append(candidate)

                if len(candidates) >= (
                    self._MAX_CANDIDATES
                ):
                    return SkillResult.succeeded(
                        skill_id=self.skill_id,
                        output=candidates,
                    )

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output=candidates,
        )
