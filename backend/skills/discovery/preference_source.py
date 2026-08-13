"""
Discovery Preference Source Contract.

Defines the provider-independent boundary used by Discovery Skills
to obtain learner preference information.

The Discovery Skills do not know whether preferences originate from:

- onboarding
- learner memory
- platform usage
- recommendation feedback
- another repository

The source implementation is responsible for that concern.

Hackathon:
    HackathonPreferenceSource

Future production:
    PlatformPreferenceSource
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class PreferenceContext:
    """
    Approved learner preference context.

    Explicit onboarding preferences are represented separately from
    behavioural enrichment so downstream components can preserve
    provenance and precedence.
    """

    topics: tuple[str, ...] = ()
    content_types: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    learning_level: str | None = None

    source: str = "unknown"

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    @property
    def is_empty(self) -> bool:
        """Return whether no preferences are available."""
        return not any(
            (
                self.topics,
                self.content_types,
                self.languages,
                self.learning_level,
            )
        )


class PreferenceSource(Protocol):
    """
    Provider-independent preference source.

    Implementations retrieve already-approved preference information.

    They must not:
    - call LLM providers
    - perform discovery
    - modify memory
    - perform uncontrolled external actions
    """

    async def get_preferences(
        self,
        user_id: str,
    ) -> PreferenceContext:
        """
        Return approved preferences for a learner.

        Parameters
        ----------
        user_id:
            Learner identifier.

        Returns
        -------
        PreferenceContext
            Approved preference context.
        """
        ...