"""
Discovery Agent.

Owns the complete Beta 1 personalised discovery workflow.

The Discovery Agent orchestrates nine bounded Discovery Skills:

1. Preference Understanding
2. Discovery Query Generation
3. Content/Product Discovery
4. Relevance Matching
5. Recommendation Ranking
6. Recommendation Explanation
7. Personalised Content Adaptation
8. Discovery Quality Verification
9. User Choice & Controlled Handoff

The Discovery Agent:

- receives Runtime ExecutionContext
- obtains approved preferences through PreferenceSource
- executes Skills explicitly and sequentially
- passes provider-independent outputs between Skills
- preserves the Runtime boundary
- stops at the explicit learner-choice boundary
- creates a controlled handoff only after explicit selection
- returns the standard AgentResult contract

The Discovery Agent does not:

- call provider SDKs directly
- bypass the Runtime
- persist memory
- modify learner preferences
- perform uncontrolled external actions
- purchase products
- automatically select recommendations

Preference architecture:

ExecutionContext
|
v
PreferenceSource
|
v
PreferenceContext
|
v
PreferenceUnderstandingSkill
|
v
DiscoveryProfile
|
v
QueryGenerationSkill
|
v
DiscoveryQuery[]
|
v
ContentProductDiscoverySkill
|
v
DiscoveryCandidate[]
|
v
RelevanceMatchingSkill
|
v
RelevanceMatch[]
|
v
RecommendationRankingSkill
|
v
RankedRecommendation[]
|
v
RecommendationExplanationSkill
|
v
RecommendationExplanation[]
|
v
PersonalisedContentAdaptationSkill
|
v
PersonalisedRecommendation[]
|
v
DiscoveryQualityVerificationSkill
|
v
VerifiedRecommendation[]
|
v
UserChoiceControlledHandoffSkill
|
+--> awaiting_user_choice
|
v
Explicit learner selection
|
v
Controlled handoff
"""

from __future__ import annotations

from typing import Any

from backend.agents.agent_manifest import AgentManifest
from backend.agents.agent_result import AgentResult
from backend.agents.base_agent import BaseAgent
from backend.runtime.context.execution_context import (
    ExecutionContext,
)

from backend.skills.discovery.hackathon_preference_source import (
    HackathonPreferenceSource,
)

from backend.skills.discovery.preference_source import (
    PreferenceContext,
    PreferenceSource,
)

from backend.skills.discovery.preference_understanding import (
    DiscoveryProfile,
    PreferenceUnderstandingSkill,
)

from backend.skills.discovery.query_generation import (
    DiscoveryQueryGenerationSkill,
)

from backend.skills.discovery.content_product_discovery import (
    ContentProductDiscoverySkill,
)

from backend.skills.discovery.relevance_matching import (
    RelevanceMatchingSkill,
)

from backend.skills.discovery.recommendation_ranking import (
    RecommendationRankingSkill,
)

from backend.skills.discovery.recommendation_explanation import (
    RecommendationExplanationSkill,
)

from backend.skills.discovery.personalised_content_adaptation import (
    PersonalisedContentAdaptationSkill,
)

from backend.skills.discovery.discovery_quality_verification import (
    DiscoveryQualityVerificationSkill,
)

from backend.skills.discovery.user_choice_handoff import (
    UserChoiceControlledHandoffSkill,
)

from backend.skills.skill import (
    SkillInput,
)


class DiscoveryAgent(BaseAgent):
    """
    Beta 1 Discovery Agent.

    Owns orchestration of the nine Discovery Skills.

    Preferences remain behind PreferenceSource.

    External discovery remains behind
    ContentProductDiscoverySkill and its DiscoveryGateway.

    The Agent itself never calls an external provider SDK.
    """

    def __init__(
        self,
        preference_skill: (
            PreferenceUnderstandingSkill | None
        ) = None,
        preference_source: (
            PreferenceSource | None
        ) = None,
        query_generation_skill: (
            DiscoveryQueryGenerationSkill | None
        ) = None,
        discovery_skill: (
            ContentProductDiscoverySkill | None
        ) = None,
        relevance_matching_skill: (
            RelevanceMatchingSkill | None
        ) = None,
        recommendation_ranking_skill: (
            RecommendationRankingSkill | None
        ) = None,
        recommendation_explanation_skill: (
            RecommendationExplanationSkill | None
        ) = None,
        personalised_content_adaptation_skill: (
            PersonalisedContentAdaptationSkill | None
        ) = None,
        quality_verification_skill: (
            DiscoveryQualityVerificationSkill | None
        ) = None,
        user_choice_handoff_skill: (
            UserChoiceControlledHandoffSkill | None
        ) = None,
    ) -> None:
        """
        Initialise the Discovery Agent.

        All Skills are injectable for deterministic testing and
        controlled Runtime composition.

        ContentProductDiscoverySkill remains optional for backward
        compatibility with the existing preference-only workflow.

        When it is not supplied, the Agent stops after producing
        the DiscoveryProfile.

        When it is supplied, the complete Beta 1 discovery pipeline
        is executed.
        """

        super().__init__(
            AgentManifest(
                agent_id="discovery_agent",
                name="Discovery Agent",
                description=(
                    "Discovers and personalises podcasts, "
                    "news, products and related content "
                    "according to approved learner "
                    "preferences."
                ),
                version="1.0.0",
            )
        )

        self.preference_skill = (
            preference_skill
            if preference_skill is not None
            else PreferenceUnderstandingSkill()
        )

        self.preference_source = (
            preference_source
            if preference_source is not None
            else HackathonPreferenceSource()
        )

        self.query_generation_skill = (
            query_generation_skill
            if query_generation_skill is not None
            else DiscoveryQueryGenerationSkill()
        )

        self.discovery_skill = (
            discovery_skill
            if discovery_skill is not None
            else None
        )

        self.relevance_matching_skill = (
            relevance_matching_skill
            if relevance_matching_skill is not None
            else RelevanceMatchingSkill()
        )

        self.recommendation_ranking_skill = (
            recommendation_ranking_skill
            if recommendation_ranking_skill is not None
            else RecommendationRankingSkill()
        )

        self.recommendation_explanation_skill = (
            recommendation_explanation_skill
            if recommendation_explanation_skill is not None
            else RecommendationExplanationSkill()
        )

        self.personalised_content_adaptation_skill = (
            personalised_content_adaptation_skill
            if personalised_content_adaptation_skill is not None
            else PersonalisedContentAdaptationSkill()
        )

        self.quality_verification_skill = (
            quality_verification_skill
            if quality_verification_skill is not None
            else DiscoveryQualityVerificationSkill()
        )

        self.user_choice_handoff_skill = (
            user_choice_handoff_skill
            if user_choice_handoff_skill is not None
            else UserChoiceControlledHandoffSkill()
        )

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        """
        Execute the Discovery workflow.

        Backward-compatible mode:

            PreferenceSource
                ↓
            PreferenceUnderstandingSkill
                ↓
            DiscoveryProfile

        Full Beta 1 mode:

            Preference Understanding
                ↓
            Query Generation
                ↓
            Content/Product Discovery
                ↓
            Relevance Matching
                ↓
            Recommendation Ranking
                ↓
            Recommendation Explanation
                ↓
            Personalised Content Adaptation
                ↓
            Quality Verification
                ↓
            User Choice / Controlled Handoff

        The full pipeline is activated when a
        ContentProductDiscoverySkill is injected.

        No recommendation is automatically selected.
        """

        validation_error = self._validate_context(
            context
        )

        if validation_error is not None:
            return validation_error

        request = context.request.strip()

        # ---------------------------------------------------------
        # Step 1 — Obtain approved learner preferences
        # ---------------------------------------------------------

        try:
            preference_context = (
                await self.preference_source.get_preferences(
                    context.user_id
                )
            )

        except (ValueError, TypeError) as exc:
            return self._failure(
                "Preference source failed: "
                f"{exc}"
            )

        if not isinstance(
            preference_context,
            PreferenceContext,
        ):
            return self._failure(
                "Preference source returned an invalid "
                "PreferenceContext."
            )

        # ---------------------------------------------------------
        # Step 2 — Preference Understanding
        # ---------------------------------------------------------

        preference_result = (
            await self.preference_skill.execute(
                SkillInput(
                    request=request,
                    user_id=context.user_id,
                    memory_context=None,
                    metadata={
                        "execution_id": context.execution_id,
                        "preference_context": (
                            preference_context
                        ),
                    },
                )
            )
        )

        if not preference_result.success:
            return self._skill_failure(
                preference_result
            )

        profile = preference_result.output

        if not isinstance(
            profile,
            DiscoveryProfile,
        ):
            return self._failure(
                "Preference Understanding returned an "
                "invalid DiscoveryProfile."
            )

        # ---------------------------------------------------------
        # Backward compatibility
        #
        # Existing Discovery Agent consumers and tests use the
        # Agent with only PreferenceSource injected.
        #
        # Do not force external discovery infrastructure onto
        # those callers.
        # ---------------------------------------------------------

        if self.discovery_skill is None:
            return AgentResult(
                success=True,
                agent_id=self.manifest.agent_id,
                output={
                    "discovery_profile": (
                        profile.as_dict()
                    ),
                    "preference_context": (
                        self._preference_context_dict(
                            preference_context
                        )
                    ),
                    "skills_executed": [
                        preference_result.skill_id,
                    ],
                    "status": "profile_ready",
                },
            )

        # ---------------------------------------------------------
        # Step 3 — Discovery Query Generation
        # ---------------------------------------------------------

        query_result = (
            await self.query_generation_skill.execute(
                SkillInput(
                    request=request,
                    user_id=context.user_id,
                    metadata={
                        "execution_id": context.execution_id,
                        "discovery_profile": profile,
                    },
                )
            )
        )

        if not query_result.success:
            return self._skill_failure(
                query_result
            )

        discovery_queries = query_result.output

        # ---------------------------------------------------------
        # Step 4 — Content/Product Discovery
        #
        # External discovery remains behind the injected
        # DiscoveryGateway-backed Skill.
        # ---------------------------------------------------------

        discovery_result = (
            await self.discovery_skill.execute(
                SkillInput(
                    request=request,
                    user_id=context.user_id,
                    metadata={
                        "execution_id": context.execution_id,
                        "discovery_queries": (
                            discovery_queries
                        ),
                    },
                )
            )
        )

        if not discovery_result.success:
            return self._skill_failure(
                discovery_result
            )

        candidates = discovery_result.output

        # ---------------------------------------------------------
        # Step 5 — Relevance Matching
        # ---------------------------------------------------------

        relevance_result = (
            await self.relevance_matching_skill.execute(
                SkillInput(
                    request=request,
                    user_id=context.user_id,
                    metadata={
                        "execution_id": context.execution_id,
                        "discovery_profile": profile,
                        "discovery_candidates": candidates,
                    },
                )
            )
        )

        if not relevance_result.success:
            return self._skill_failure(
                relevance_result
            )

        relevance_matches = relevance_result.output

        # ---------------------------------------------------------
        # Step 6 — Recommendation Ranking
        # ---------------------------------------------------------

        ranking_result = (
            await self.recommendation_ranking_skill.execute(
                SkillInput(
                    request=request,
                    user_id=context.user_id,
                    metadata={
                        "execution_id": context.execution_id,
                        "relevance_matches": (
                            relevance_matches
                        ),
                    },
                )
            )
        )

        if not ranking_result.success:
            return self._skill_failure(
                ranking_result
            )

        ranked_recommendations = (
            ranking_result.output
        )

        # ---------------------------------------------------------
        # Step 7 — Recommendation Explanation
        # ---------------------------------------------------------

        explanation_result = (
            await self.recommendation_explanation_skill.execute(
                SkillInput(
                    request=request,
                    user_id=context.user_id,
                    metadata={
                        "execution_id": context.execution_id,
                        "ranked_recommendations": (
                            ranked_recommendations
                        ),
                    },
                )
            )
        )

        if not explanation_result.success:
            return self._skill_failure(
                explanation_result
            )

        recommendation_explanations = (
            explanation_result.output
        )

        # ---------------------------------------------------------
        # Step 8 — Personalised Content Adaptation
        # ---------------------------------------------------------

        adaptation_result = (
            await self.personalised_content_adaptation_skill.execute(
                SkillInput(
                    request=request,
                    user_id=context.user_id,
                    metadata={
                        "execution_id": context.execution_id,
                        "discovery_profile": profile,
                        "recommendation_explanations": (
                            recommendation_explanations
                        ),
                    },
                )
            )
        )

        if not adaptation_result.success:
            return self._skill_failure(
                adaptation_result
            )

        personalised_recommendations = (
            adaptation_result.output
        )

        # ---------------------------------------------------------
        # Step 9 — Discovery Quality Verification
        # ---------------------------------------------------------

        quality_result = (
            await self.quality_verification_skill.execute(
                SkillInput(
                    request=request,
                    user_id=context.user_id,
                    metadata={
                        "execution_id": context.execution_id,
                        "personalised_recommendations": (
                            personalised_recommendations
                        ),
                    },
                )
            )
        )

        if not quality_result.success:
            return self._skill_failure(
                quality_result
            )

        quality_output = quality_result.output

        if not isinstance(
            quality_output,
            dict,
        ):
            return self._failure(
                "Discovery Quality Verification returned "
                "an invalid output."
            )

        verified_recommendations = (
            quality_output.get(
                "verified",
                [],
            )
        )

        # ---------------------------------------------------------
        # Step 10 — User Choice & Controlled Handoff
        # ---------------------------------------------------------

        selected_option_id = (
            context.metadata.get(
                "selected_option_id"
            )
        )

        handoff_result = (
            await self.user_choice_handoff_skill.execute(
                SkillInput(
                    request=request,
                    user_id=context.user_id,
                    metadata={
                        "execution_id": context.execution_id,
                        "verified_recommendations": (
                            verified_recommendations
                        ),
                        "selected_option_id": (
                            selected_option_id
                        ),
                    },
                )
            )
        )

        if not handoff_result.success:
            return self._skill_failure(
                handoff_result
            )

        handoff_output = handoff_result.output

        if not isinstance(
            handoff_output,
            dict,
        ):
            return self._failure(
                "User Choice Controlled Handoff returned "
                "an invalid output."
            )

        # ---------------------------------------------------------
        # Final AgentResult
        #
        # Preserve domain objects at the Agent boundary.
        #
        # Transport serialization belongs to the application/API
        # boundary. In particular, ControlledHandoff must remain a
        # domain object so consumers can use its explicit contract.
        # ---------------------------------------------------------

        return AgentResult(
            success=True,
            agent_id=self.manifest.agent_id,
            output={
                "status": handoff_output.get(
                    "status"
                ),
                "discovery_profile": (
                    profile.as_dict()
                ),
                "preference_context": (
                    self._preference_context_dict(
                        preference_context
                    )
                ),
                "discovery_queries": (
                    self._serialise_items(
                        discovery_queries
                    )
                ),
                "candidates": (
                    self._serialise_items(
                        candidates
                    )
                ),
                "relevance_matches": (
                    self._serialise_items(
                        relevance_matches
                    )
                ),
                "ranked_recommendations": (
                    self._serialise_items(
                        ranked_recommendations
                    )
                ),
                "recommendation_explanations": (
                    self._serialise_items(
                        recommendation_explanations
                    )
                ),
                "personalised_recommendations": (
                    self._serialise_items(
                        personalised_recommendations
                    )
                ),
                "quality": (
                    self._serialise_value(
                        quality_output
                    )
                ),

                # Handoff options are intentionally preserved
                # as domain objects for the learner-choice
                # boundary.
                "options": (
                    handoff_output.get(
                        "options",
                        [],
                    )
                ),

                # ControlledHandoff must remain the domain
                # object rather than being converted to a dict.
                "handoff": (
                    handoff_output.get(
                        "handoff"
                    )
                ),

                # Preserve the complete Skill output for
                # compatibility with existing consumers.
                "user_choice": handoff_output,

                "skills_executed": [
                    preference_result.skill_id,
                    query_result.skill_id,
                    discovery_result.skill_id,
                    relevance_result.skill_id,
                    ranking_result.skill_id,
                    explanation_result.skill_id,
                    adaptation_result.skill_id,
                    quality_result.skill_id,
                    handoff_result.skill_id,
                ],
            },
        )

    def _validate_context(
        self,
        context: ExecutionContext | None,
    ) -> AgentResult | None:
        """
        Validate the Runtime execution context.
        """

        if context is None:
            return self._failure(
                "Execution context cannot be None."
            )

        if not isinstance(
            context.request,
            str,
        ):
            return self._failure(
                "Execution context request must be a string."
            )

        if not context.request.strip():
            return self._failure(
                "Execution context request cannot be empty."
            )

        return None

    def _failure(
        self,
        error: str,
        *,
        output: Any = None,
    ) -> AgentResult:
        """
        Create a standard failed AgentResult.
        """

        return AgentResult(
            success=False,
            agent_id=self.manifest.agent_id,
            output=output,
            error=error,
        )

    def _skill_failure(
        self,
        skill_result: Any,
    ) -> AgentResult:
        """
        Convert a failed SkillResult into AgentResult.
        """

        return self._failure(
            (
                f"Skill '{skill_result.skill_id}' failed: "
                f"{skill_result.error}"
            ),
            output={
                "skill_id": skill_result.skill_id,
                "error": skill_result.error,
            },
        )

    @staticmethod
    def _preference_context_dict(
        preference_context: PreferenceContext,
    ) -> dict[str, object]:
        """
        Convert PreferenceContext into a serialisable payload.
        """

        return {
            "topics": list(
                preference_context.topics
            ),
            "content_types": list(
                preference_context.content_types
            ),
            "languages": list(
                preference_context.languages
            ),
            "learning_level": (
                preference_context.learning_level
            ),
            "source": preference_context.source,
        }

    @staticmethod
    def _serialise_value(
        value: Any,
    ) -> Any:
        """
        Convert Skill output objects into transport-safe data.

        Objects exposing as_dict() use that contract.

        Lists, tuples and dictionaries are recursively serialised.
        """

        if hasattr(
            value,
            "as_dict",
        ):
            return value.as_dict()

        if isinstance(
            value,
            (list, tuple),
        ):
            return [
                DiscoveryAgent._serialise_value(
                    item
                )
                for item in value
            ]

        if isinstance(
            value,
            dict,
        ):
            return {
                key: DiscoveryAgent._serialise_value(
                    item
                )
                for key, item in value.items()
            }

        return value

    @staticmethod
    def _serialise_items(
        values: Any,
    ) -> list[Any]:
        """
        Serialise a sequence of Skill outputs.
        """

        if not isinstance(
            values,
            (list, tuple),
        ):
            return []

        return [
            DiscoveryAgent._serialise_value(
                value
            )
            for value in values
        ]