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

from src.ai_runtime.discovery.flash_deal_demo import (
    build_demo_deal,
    build_demo_memory,
)

from src.ai_runtime.discovery.service import (
    CharacterContext,
    DiscoveryRequest,
    DiscoveryService,
)

from src.ai_runtime.discovery.notification import (
    DiscoveryNotification,
)

from src.ai_runtime.discovery.flash_deal_presenter import (
    FlashDealPresenter,
)

from src.ai_runtime.commerce.flash_deal_commerce import (
    FlashDealCommerce,
)

from src.ai_runtime.commerce.service import (
    CommerceService,
)

from src.ai_runtime.commerce.models import (
    CommerceActionStatus,
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
    # STEP 4 — PERSONALISED FLASH DEAL
    # -----------------------------------------------------------------------

    print("STEP 4 — PERSONALISED DISCOVERY")
    print("-" * 72)
    print(
        "Yeti found something that matches "
        "what this learner likes."
    )
    print(
        "Here is the personalised discovery:"
    )
    print()

    # Build the same domain inputs that a real discovery
    # application flow would receive.
    demo_deal = build_demo_deal()
    demo_memory = build_demo_memory()

    discovery_request = DiscoveryRequest(
        user_id=demo_memory.user_id,
        deal=demo_deal,
        character=CharacterContext(
            character_id="yeti",
            character_name="Yeti",
            message=(
                "Look what I found! "
                "This could be perfect for you."
            ),
        ),
        product_image_url=(
            "https://example.com/demo/iphone17-pro.jpg"
        ),
        tagline="Pro. Beautiful. Powerful.",
        highlights=(
            "Pro camera system",
            "High-performance chip",
            "All-day battery life",
            "Premium display",
        ),
    )

    flash_deal_card = DiscoveryService().create_flash_deal(
        discovery_request,
        memories=[demo_memory],
    )

    print(
        FlashDealPresenter().render(
            flash_deal_card
        )
    )

    # -----------------------------------------------------------------------
    # STEP 4A — CHARACTER DISCOVERY NOTIFICATION
    # -----------------------------------------------------------------------

    discovery_notification = (
        DiscoveryNotification.from_flash_deal(
            notification_id="demo-notification-001",
            user_id=demo_memory.user_id,
            deal=flash_deal_card,
        )
    )

    print()
    print("CHARACTER NOTIFICATION")
    print("-" * 72)
    print(
        discovery_notification.render()
    )
    print()

    assert (
        discovery_notification.user_id
        == demo_memory.user_id
    )
    assert (
        discovery_notification.character_id
        == flash_deal_card.character_id
    )
    assert (
        discovery_notification.deal
        is flash_deal_card
    )

    assert flash_deal_card.character_id == "yeti"
    assert flash_deal_card.deal_id == demo_deal.deal_id
    assert flash_deal_card.product_name
    assert demo_memory.user_id == "demo-user"
    assert flash_deal_card.relevance_reason
    assert flash_deal_card.get_deal_url
    assert flash_deal_card.more_information_url

    # -----------------------------------------------------------------------
    # STEP 5 — COMMERCE ACTION
    # -----------------------------------------------------------------------

    print(
        "The learner can now inspect the vendor "
        "information or proceed through the deal link."
    )
    print()

    print("STEP 5 — COMMERCE ACTION")
    print("-" * 72)

    commerce_action = FlashDealCommerce().create_action(
        user_id="demo-user",
        card=flash_deal_card,
    )

    print(
        f"Product: {flash_deal_card.product_name}"
    )
    print(
        f"Vendor: {flash_deal_card.vendor_name}"
    )
    print(
        f"Commerce action: "
        f"{commerce_action.action_type.value.upper()}"
    )

    commerce_result = CommerceService().initiate(
        commerce_action
    )

    print(
        f"Status: "
        f"{commerce_result.status.value.upper()}"
    )

    print()
    print("GET DEAL")
    print("  -> Approved commerce boundary")
    print("  -> Vendor handoff")
    print()
    print(
        "Payment is not executed in the hackathon demo."
    )

    assert (
        commerce_result.status
        == CommerceActionStatus.REDIRECT
    )
    assert (
        commerce_result.deal_id
        == flash_deal_card.deal_id
    )
    assert (
        commerce_result.next_url
        == flash_deal_card.get_deal_url
    )

    # -----------------------------------------------------------------------
    # STEP 6 — Final result
    # -----------------------------------------------------------------------

    print()
    print("=" * 72)

    if evaluation_result.passed:
        print("HACKATHON DEMO: SUCCESS")
        print()
        # ASCII-safe output keeps the executable reliable when
        # stdout is captured by Windows pytest/subprocess.
        # Preserve the stable hackathon readiness marker.
        print(
            "Governance -> Intelligence -> Learning -> Evaluation"
        )
        print(
            "Governance -> Intelligence -> Learning -> "
            "Evaluation -> Personalised Discovery"
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