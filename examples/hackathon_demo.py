"""
EasyChatBot Hackathon — Unified Demonstration.

Demonstrates the four completed hackathon capabilities:

1. Governance
2. Live Intelligence
3. Learning Challenge
4. Quality Evaluation

Architecture:

User Request
     |
     v
Governance Check
     |
     +---- BLOCK -> Stop
     |
     v
Live Intelligence
     |
     v
Learning Challenge
     |
     v
Quality Evaluation
     |
     v
Final Demonstration Result

This file is an orchestration/demo layer only.

It does not modify:
- Conversation Agent
- Live Intelligence Agent
- Challenge Engine
- Evaluation Engine
- Governance Engine
- Parallel Provider
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Repository path bootstrap
# ---------------------------------------------------------------------------

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
    LiveIntelligenceRequest,
)

from src.challenge_engine.generator import (
    ChallengeGenerator,
)

from src.challenge_engine.models import (
    DiscussionQuestion,
    LearningChallenge,
    VocabularyItem,
)

from src.evaluation.criteria import (
    COMPLETENESS,
    EDUCATIONAL_VALUE,
    LANGUAGE_LEVEL,
    SOURCE_COVERAGE,
)

from src.evaluation.deterministic_evaluator import (
    DeterministicEvaluator,
)

from src.evaluation.engine import (
    EvaluationEngine,
)

from src.evaluation.report import (
    EvaluationReport,
)

from src.governance.engine import (
    GovernancePolicyEngine,
)

from src.governance.models import (
    GovernanceDecision,
    GovernancePolicy,
    RiskLevel,
)

from src.providers.search_provider.interface import (
    SearchResult,
)


class DemoSearchProvider:
    """
    Controlled search provider for the unified demo.

    The real Parallel provider is already validated separately
    by H1 integration tests.

    This keeps the unified demo deterministic and suitable for
    repeatable hackathon demonstrations.
    """

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:

        return [
            SearchResult(
                title="European AI Act — Demo Source",
                url="https://example.com/ai-act",
                content=(
                    "The European Union AI Act establishes "
                    "a risk-based framework for artificial "
                    "intelligence."
                ),
                source="demo-provider",
            )
        ]


class DemoIntelligenceProcessor:
    """
    Controlled intelligence processor.

    The real provider-backed intelligence flow is validated
    separately in H1.
    """

    async def summarise(
        self,
        results: list[SearchResult],
        language: str,
        learner_level: str,
    ) -> tuple[str, list[str]]:

        return (
            "The European Union AI Act establishes "
            "a risk-based framework for artificial "
            "intelligence.",
            [
                "AI governance",
                "risk management",
                "compliance",
            ],
        )


class DemoChallengeContentGenerator:
    """
    Controlled educational content generator.
    """

    async def generate_vocabulary(
        self,
        summary: str,
        language: str,
        learner_level: str,
    ) -> list[VocabularyItem]:

        return [
            VocabularyItem(
                term="gouvernance",
                definition=(
                    "La manière dont une organisation "
                    "est dirigée et contrôlée."
                ),
                example=(
                    "La gouvernance de l'IA devient "
                    "essentielle."
                ),
            ),
            VocabularyItem(
                term="réglementation",
                definition=(
                    "Ensemble des règles qui encadrent "
                    "une activité."
                ),
                example=(
                    "La réglementation européenne évolue."
                ),
            ),
        ]

    async def generate_questions(
        self,
        summary: str,
        language: str,
        learner_level: str,
    ) -> list[DiscussionQuestion]:

        return [
            DiscussionQuestion(
                question=(
                    "Pourquoi la réglementation de "
                    "l'IA est-elle importante ?"
                ),
                difficulty=learner_level,
            ),
            DiscussionQuestion(
                question=(
                    "Quels sont les avantages d'une "
                    "réglementation européenne de l'IA ?"
                ),
                difficulty=learner_level,
            ),
        ]


def create_governance_policy() -> GovernancePolicy:
    """
    Governance policy for the live intelligence demo.

    Live research may access external information but
    must never create external side effects.
    """

    return GovernancePolicy(
        capability="live_intelligence_research",
        risk_level=RiskLevel.MEDIUM,
        requires_human_review=False,
        allows_external_calls=True,
        allows_side_effects=False,
    )


async def create_learning_challenge() -> LearningChallenge:
    """
    Execute the H1 learning challenge flow.
    """

    intelligence_agent = LiveIntelligenceAgent(
        search_provider=DemoSearchProvider(),
        processor=DemoIntelligenceProcessor(),
    )

    intelligence = await intelligence_agent.execute(
        LiveIntelligenceRequest(
            topic="AI Act",
            language="French",
            learner_level="B2",
        )
    )

    challenge_generator = ChallengeGenerator(
        content_generator=DemoChallengeContentGenerator()
    )

    return await challenge_generator.generate(
        intelligence=intelligence,
        language="French",
        learner_level="B2",
    )


async def run_demo() -> None:
    """
    Execute the complete hackathon demonstration.
    """

    print()
    print("=" * 72)
    print("EasyChatBot — HACKATHON DEMONSTRATION")
    print("=" * 72)
    print()

    # -----------------------------------------------------------------------
    # STEP 1 — Governance
    # -----------------------------------------------------------------------

    print("STEP 1 — GOVERNANCE")
    print("-" * 72)

    governance_engine = GovernancePolicyEngine()

    governance_result = governance_engine.evaluate(
        create_governance_policy()
    )

    print(
        f"Capability: {governance_result.capability}"
    )

    print(
        f"Risk level: "
        f"{governance_result.risk_level.value}"
    )

    print(
        f"Decision: "
        f"{governance_result.decision.value.upper()}"
    )

    if governance_result.decision != GovernanceDecision.ALLOW:
        raise RuntimeError(
            "Hackathon demo stopped because governance "
            "did not allow the capability."
        )

    print("Governance check: PASSED")
    print()

    # -----------------------------------------------------------------------
    # STEP 2 — Live Intelligence + Challenge
    # -----------------------------------------------------------------------

    print("STEP 2 — LIVE INTELLIGENCE")
    print("-" * 72)

    challenge = await create_learning_challenge()

    print(f"Topic: {challenge.topic}")
    print(f"Language: {challenge.language}")
    print(f"Learner level: {challenge.learner_level}")
    print()

    print("Summary:")
    print(challenge.summary)
    print()

    print("Vocabulary:")

    for item in challenge.vocabulary:
        print(f"  • {item.term}: {item.definition}")

    print()

    print("Discussion questions:")

    for index, question in enumerate(
        challenge.discussion_questions,
        start=1,
    ):
        print(
            f"  {index}. {question.question}"
        )

    print()

    # -----------------------------------------------------------------------
    # STEP 3 — Quality Evaluation
    # -----------------------------------------------------------------------

    print("STEP 3 — AI QUALITY EVALUATION")
    print("-" * 72)

    evaluator = DeterministicEvaluator()

    criterion_scores = evaluator.evaluate(
        challenge
    )

    evaluation_engine = EvaluationEngine(
        criteria=[
            COMPLETENESS,
            LANGUAGE_LEVEL,
            EDUCATIONAL_VALUE,
            SOURCE_COVERAGE,
        ],
        passing_score=0.70,
    )

    evaluation_result = evaluation_engine.evaluate(
        criterion_scores
    )

    report = EvaluationReport().generate(
        evaluation_result
    )

    print(report)

    # -----------------------------------------------------------------------
    # STEP 4 — Final result
    # -----------------------------------------------------------------------

    print()
    print("=" * 72)

    if evaluation_result.passed:
        print("HACKATHON DEMO: SUCCESS")
        print()
        # ASCII-safe output keeps the executable reliable when
        # stdout is captured by Windows pytest/subprocess.
        print(
            "Governance -> Intelligence -> Learning -> Evaluation"
        )
        print(
            "All demonstrated capabilities completed successfully."
        )
    else:
        print("HACKATHON DEMO: QUALITY CHECK FAILED")

    print("=" * 72)
    print()

    assert governance_result.decision == GovernanceDecision.ALLOW
    assert challenge.topic == "AI Act"
    assert evaluation_result.passed is True


def main() -> None:
    """
    Application entry point.
    """

    asyncio.run(run_demo())


if __name__ == "__main__":
    main()