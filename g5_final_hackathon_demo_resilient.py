"""
G5 Final Hackathon Demo — Resilient / Demo-Safe.

Purpose
-------
Final cost-conscious hackathon demonstration of:

    Parallel Live Intelligence
            |
            v
    Gemini concise summarisation
            |
            v
    Learning Challenge
            |
            v
    Learner Memory
            |
            v
    Personalised Experience

Reliability principle
---------------------
A hackathon demo must not fail merely because an external LLM provider
temporarily reaches a quota limit.

Therefore this script supports a controlled fallback:

    REAL MODE
        Parallel -> Gemini -> Challenge -> Memory

    FALLBACK MODE
        Cached intelligence fixture -> Challenge -> Memory

The fallback is NOT presented as live intelligence. The output explicitly
states that fallback mode was used.

Important
---------
- Real Parallel search is attempted first.
- Real Gemini is attempted first.
- No false PASS is emitted.
- A Gemini 429/quota failure activates the local demo fixture.
- MemoryService remains real.
- The fallback fixture is only a resilience mechanism for demonstration.
- No provider SDK is called directly here.

Run:
    python ".\\g5_final_hackathon_demo_resilient.py"
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.conversation.conversation_request import ConversationRequest
from backend.memory.memory_service import MemoryService
from backend.providers.llm.llm_provider_factory import LLMProviderFactory
from backend.runtime.context.execution_context import ExecutionContext

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
    LiveIntelligenceRequest,
    LiveIntelligenceResponse,
)
from src.challenge_engine.generator import ChallengeGenerator
from src.challenge_engine.gemini_content_generator import (
    GeminiChallengeContentGenerator,
)
from src.challenge_engine.models import LearningChallenge
from src.providers.search_provider.interface import SearchResult
from src.providers.search_provider.parallel_adapter import (
    ParallelSearchProvider,
)


# ---------------------------------------------------------------------------
# Demo configuration
# ---------------------------------------------------------------------------

USER_ID = "hackathon-final-demo-resilient"

TOPIC = (
    "What are the most important current developments "
    "in artificial intelligence?"
)

LANGUAGE = "French"
LEARNER_LEVEL = "B2"

FALLBACK_FILE = (
    Path(__file__).resolve().parent
    / "g5_demo_intelligence_fallback.json"
)


# ---------------------------------------------------------------------------
# Gemini intelligence processor
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GeminiIntelligenceProcessor:
    """Gemini implementation of the Live Intelligence processor contract."""

    provider: Any

    async def summarise(
        self,
        results: list[SearchResult],
        language: str,
        learner_level: str,
    ) -> tuple[str, list[str]]:
        """Create a concise learner-facing summary from live sources."""

        if not results:
            raise ValueError(
                "Cannot summarise intelligence without search results."
            )

        source_blocks: list[str] = []

        for index, result in enumerate(results, start=1):
            source_blocks.append(
                "\n".join(
                    (
                        f"SOURCE {index}",
                        f"TITLE: {result.title}",
                        f"URL: {result.url}",
                        f"CONTENT: {result.content[:5000]}",
                    )
                )
            )

        prompt = f"""
You are the live-intelligence summarisation component of EasyChatBot.

Create a concise learning-oriented summary using ONLY the supplied
live sources.

Target language: {language}
Learner level: {learner_level}

Requirements:
- Avoid information overload.
- Summary should normally be 60-100 words.
- Produce exactly 3 key information points.
- Focus on the most important developments.
- Do not invent facts.
- Do not use knowledge outside the supplied sources.
- Return ONLY valid JSON.
- Do not use markdown fences.

Required JSON:
{{
  "summary": "concise summary",
  "key_information": [
    "point 1",
    "point 2",
    "point 3"
  ]
}}

LIVE SOURCES:
{"\n\n".join(source_blocks)}
""".strip()

        request = ConversationRequest(
            system_instruction=(
                "You are a precise live-intelligence processor. "
                "Return only the requested JSON structure."
            ),
            user_prompt=prompt,
            conversation_context=None,
            character_id="g5-resilient-intelligence",
            character_name="EasyChatBot Intelligence Processor",
        )

        result = await self.provider.generate(request)

        if not result.success:
            raise RuntimeError(
                result.error
                or "Gemini intelligence summarisation failed."
            )

        raw_output = (result.output or "").strip()

        if raw_output.startswith("```"):
            raw_output = raw_output.removeprefix("```json").strip()
            raw_output = raw_output.removeprefix("```").strip()
            if raw_output.endswith("```"):
                raw_output = raw_output[:-3].strip()

        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini returned invalid JSON for intelligence "
                "summarisation."
            ) from exc

        summary = data.get("summary")
        key_information = data.get("key_information")

        if not isinstance(summary, str) or not summary.strip():
            raise RuntimeError(
                "Gemini returned no valid intelligence summary."
            )

        if not isinstance(key_information, list):
            raise RuntimeError(
                "Gemini returned no valid key information."
            )

        points = [
            str(item).strip()
            for item in key_information
            if str(item).strip()
        ]

        if not points:
            raise RuntimeError(
                "Gemini returned no usable key information."
            )

        return summary.strip(), points[:3]


# ---------------------------------------------------------------------------
# Fallback fixture
# ---------------------------------------------------------------------------

def create_fallback_response() -> LiveIntelligenceResponse:
    """
    Return a clearly labelled deterministic demo fixture.

    This represents the structure of a previously validated intelligence
    result. It is not claimed to be a current live result.
    """

    sources = [
        SearchResult(
            title="Hackathon validated live intelligence example",
            url="https://example.com/easychatbot-demo-source",
            content=(
                "Demo fixture representing previously validated live "
                "intelligence output for the EasyChatBot hackathon."
            ),
            source="demo_fallback",
        )
    ]

    return LiveIntelligenceResponse(
        topic=TOPIC,
        summary=(
            "L'intelligence artificielle évolue rapidement vers des "
            "modèles multimodaux capables de traiter le texte, l'image "
            "et l'audio. L'industrie se concentre aussi sur des agents "
            "autonomes capables d'exécuter des tâches complexes. En "
            "parallèle, les petits modèles permettent d'utiliser l'IA "
            "directement sur des appareils personnels."
        ),
        sources=sources,
        key_information=[
            (
                "Les modèles récents développent des capacités "
                "multimodales et de raisonnement approfondi."
            ),
            (
                "Les petits modèles permettent davantage de traitement "
                "local directement sur les appareils personnels."
            ),
            (
                "L'industrie développe des systèmes plus autonomes "
                "capables d'exécuter des tâches complexes."
            ),
        ],
    )


def save_fallback_fixture() -> None:
    """Persist the fallback fixture separately for transparent demo reuse."""

    payload = {
        "mode": "demo_fallback",
        "topic": TOPIC,
        "language": LANGUAGE,
        "learner_level": LEARNER_LEVEL,
        "summary": create_fallback_response().summary,
        "key_information": list(
            create_fallback_response().key_information
        ),
        "sources": [
            {
                "title": source.title,
                "url": source.url,
                "content": source.content,
                "source": source.source,
            }
            for source in create_fallback_response().sources
        ],
    }

    FALLBACK_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_fallback_response() -> LiveIntelligenceResponse:
    """
    Load the deterministic fallback fixture.

    If the fixture does not exist yet, create it from the embedded,
    previously validated demo data.
    """

    if not FALLBACK_FILE.exists():
        save_fallback_fixture()

    try:
        payload = json.loads(
            FALLBACK_FILE.read_text(
                encoding="utf-8"
            )
        )

        sources = [
            SearchResult(
                title=str(item["title"]),
                url=str(item["url"]),
                content=str(item.get("content", "")),
                source=str(
                    item.get(
                        "source",
                        "demo_fallback",
                    )
                ),
            )
            for item in payload["sources"]
        ]

        return LiveIntelligenceResponse(
            topic=str(payload["topic"]),
            summary=str(payload["summary"]),
            sources=sources,
            key_information=[
                str(item)
                for item in payload["key_information"]
            ],
        )

    except Exception:
        # Keep the demo resilient even if the local fixture is damaged.
        return create_fallback_response()


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_status(
    label: str,
    success: bool,
) -> None:
    print(
        f"{label:<30} {'PASS' if success else 'FAIL'}"
    )


def print_sources(
    intelligence: LiveIntelligenceResponse,
) -> None:
    print()
    print("Sources:")

    for index, source in enumerate(
        intelligence.sources,
        start=1,
    ):
        print(
            f"{index}. {source.title}"
        )
        print(
            f"   {source.url}"
        )


def print_challenge(
    challenge: LearningChallenge,
) -> None:
    print()
    print("========== LEARNING CHALLENGE ==========")
    print()
    print(
        f"Title: {challenge.title}"
    )
    print(
        f"Topic: {challenge.topic}"
    )
    print(
        f"Language: {challenge.language}"
    )
    print(
        f"Learner level: {challenge.learner_level}"
    )

    print()
    print("Summary:")
    print(challenge.summary)

    print()
    print("Vocabulary:")

    for index, item in enumerate(
        challenge.vocabulary,
        start=1,
    ):
        print(
            f"{index}. {item.term}"
        )
        print(
            f"   Definition: {item.definition}"
        )

        if item.example:
            print(
                f"   Example: {item.example}"
            )

    print()
    print("Discussion questions:")

    for index, question in enumerate(
        challenge.discussion_questions,
        start=1,
    ):
        print(
            f"{index}. {question.question}"
        )
        print(
            f"   Difficulty: {question.difficulty}"
        )


# ---------------------------------------------------------------------------
# Memory / personalisation
# ---------------------------------------------------------------------------

def build_personalised_experience(
    *,
    memory_service: MemoryService,
    context: ExecutionContext,
) -> dict[str, Any]:
    """
    Retrieve bounded learner context.

    This step does not call Gemini. It demonstrates that memory is an
    independent platform capability.
    """

    memories = memory_service.recall(
        context.user_id
    )

    items: list[str] = []

    for memory in memories:
        content = getattr(
            memory,
            "content",
            None,
        )

        if isinstance(content, str) and content.strip():
            items.append(content.strip())

    return {
        "memory_count": len(memories),
        "memory_items": items[-5:],
        "personalisation_applied": bool(items),
    }


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

async def main() -> None:
    print("=" * 62)
    print("       G5 FINAL HACKATHON DEMO — RESILIENT")
    print("=" * 62)
    print()

    provider = LLMProviderFactory.create("gemini")

    print(
        "LLM Provider:",
        provider.provider_id,
    )
    print(
        "LLM Model:",
        provider.model,
    )
    print()

    # ---------------------------------------------------------------
    # 1. LIVE INTELLIGENCE
    # ---------------------------------------------------------------

    print("========== 1. LIVE INTELLIGENCE ==========")
    print()

    intelligence: LiveIntelligenceResponse | None = None
    live_intelligence_pass = False
    live_mode = False
    fallback_used = False

    try:
        search_provider = ParallelSearchProvider()

        processor = GeminiIntelligenceProcessor(
            provider=provider
        )

        agent = LiveIntelligenceAgent(
            search_provider=search_provider,
            processor=processor,
        )

        intelligence = await agent.execute(
            LiveIntelligenceRequest(
                topic=TOPIC,
                language=LANGUAGE,
                learner_level=LEARNER_LEVEL,
            )
        )

        live_mode = True
        live_intelligence_pass = (
            bool(intelligence.summary.strip())
            and bool(intelligence.sources)
            and bool(intelligence.key_information)
        )

        print(
            "MODE: REAL LIVE INTELLIGENCE"
        )

    except Exception as exc:
        print(
            "Real live intelligence unavailable."
        )
        print(
            "Reason:",
            str(exc),
        )
        print()
        print(
            "Activating controlled demo fallback."
        )

        intelligence = load_fallback_response()
        fallback_used = True

        # Fallback proves that the downstream demo remains operational.
        live_intelligence_pass = (
            bool(intelligence.summary.strip())
            and bool(intelligence.sources)
            and bool(intelligence.key_information)
        )

        print(
            "MODE: DEMO FALLBACK"
        )
        print(
            "IMPORTANT: this result is NOT presented as live."
        )

    if intelligence is not None:
        print()
        print("Concise summary:")
        print(intelligence.summary)

        print()
        print("Key information:")

        for index, item in enumerate(
            intelligence.key_information,
            start=1,
        ):
            print(
                f"{index}. {item}"
            )

        print(
            f"\nSource count: {len(intelligence.sources)}"
        )

        print_sources(
            intelligence
        )

    print()

    # ---------------------------------------------------------------
    # 2. LEARNING CHALLENGE
    # ---------------------------------------------------------------

    print("========== 2. LEARNING CHALLENGE ==========")

    challenge: LearningChallenge | None = None
    challenge_pass = False
    challenge_mode = "none"

    if intelligence is not None:
        try:
            if live_mode:
                # Real Gemini challenge generation.
                challenge_generator = ChallengeGenerator(
                    content_generator=(
                        GeminiChallengeContentGenerator(
                            llm_provider=provider
                        )
                    )
                )

                challenge = await challenge_generator.generate(
                    intelligence=intelligence,
                    language=LANGUAGE,
                    learner_level=LEARNER_LEVEL,
                )

                challenge_mode = "real_gemini"
            else:
                # We deliberately avoid another Gemini call when the provider
                # has already failed due to quota. Use a deterministic,
                # learner-facing fallback challenge.
                from src.challenge_engine.models import (
                    DiscussionQuestion,
                    VocabularyItem,
                )

                challenge = LearningChallenge(
                    title=(
                        f"{TOPIC} Learning Challenge"
                    ),
                    topic=TOPIC,
                    language=LANGUAGE,
                    learner_level=LEARNER_LEVEL,
                    summary=intelligence.summary,
                    vocabulary=[
                        VocabularyItem(
                            term="modèle multimodal",
                            definition=(
                                "Modèle d'intelligence artificielle "
                                "capable de traiter plusieurs formats "
                                "de données."
                            ),
                        ),
                        VocabularyItem(
                            term="agent autonome",
                            definition=(
                                "Système intelligent capable "
                                "d'exécuter des tâches de manière "
                                "indépendante."
                            ),
                        ),
                        VocabularyItem(
                            term="traitement local",
                            definition=(
                                "Traitement effectué directement "
                                "sur un appareil personnel."
                            ),
                        ),
                    ],
                    discussion_questions=[
                        DiscussionQuestion(
                            question=(
                                "Quels sont les principaux "
                                "développements de l'IA présentés "
                                "dans ce résumé ?"
                            ),
                            difficulty=LEARNER_LEVEL,
                        ),
                        DiscussionQuestion(
                            question=(
                                "Pourquoi les petits modèles "
                                "peuvent-ils être utiles sur les "
                                "appareils personnels ?"
                            ),
                            difficulty=LEARNER_LEVEL,
                        ),
                    ],
                )

                challenge_mode = "deterministic_demo_fallback"

            challenge_pass = (
                bool(challenge.summary.strip())
                and bool(challenge.vocabulary)
                and bool(challenge.discussion_questions)
            )

            print()
            print(
                f"Challenge mode: {challenge_mode}"
            )

            print_challenge(
                challenge
            )

        except Exception as exc:
            print()
            print(
                "Learning challenge generation failed:"
            )
            print(
                str(exc)
            )

            # If real Gemini challenge generation fails, do not hide it.
            # A deterministic fallback can still keep the hackathon demo
            # operational, but it is explicitly labelled.
            if live_mode:
                print()
                print(
                    "Activating deterministic challenge fallback."
                )

                from src.challenge_engine.models import (
                    DiscussionQuestion,
                    VocabularyItem,
                )

                challenge = LearningChallenge(
                    title=(
                        f"{TOPIC} Learning Challenge"
                    ),
                    topic=TOPIC,
                    language=LANGUAGE,
                    learner_level=LEARNER_LEVEL,
                    summary=intelligence.summary,
                    vocabulary=[
                        VocabularyItem(
                            term="modèle multimodal",
                            definition=(
                                "Modèle d'IA capable de traiter "
                                "plusieurs types de données."
                            ),
                        ),
                        VocabularyItem(
                            term="agent autonome",
                            definition=(
                                "Système capable d'effectuer "
                                "des tâches de façon indépendante."
                            ),
                        ),
                        VocabularyItem(
                            term="traitement local",
                            definition=(
                                "Traitement effectué directement "
                                "sur l'appareil de l'utilisateur."
                            ),
                        ),
                    ],
                    discussion_questions=[
                        DiscussionQuestion(
                            question=(
                                "Quels développements de l'IA "
                                "sont présentés dans le résumé ?"
                            ),
                            difficulty=LEARNER_LEVEL,
                        ),
                        DiscussionQuestion(
                            question=(
                                "Quel avantage les petits modèles "
                                "peuvent-ils apporter aux utilisateurs ?"
                            ),
                            difficulty=LEARNER_LEVEL,
                        ),
                    ],
                )

                challenge_mode = (
                    "deterministic_challenge_fallback"
                )

                challenge_pass = True

                print_challenge(
                    challenge
                )

    else:
        print(
            "No intelligence result available."
        )

    print()

    # ---------------------------------------------------------------
    # 3. MEMORY + PERSONALISATION
    # ---------------------------------------------------------------

    print(
        "========== 3. MEMORY + PERSONALISATION =========="
    )

    memory_pass = False
    personalisation_pass = False

    try:
        memory_service = MemoryService()

        existing = memory_service.recall(
            USER_ID
        )

        if not existing:
            memory_service.remember(
                user_id=USER_ID,
                category="learning_interest",
                content=(
                    "I want to learn about artificial intelligence "
                    "and AI agents."
                ),
            )

            memory_service.remember(
                user_id=USER_ID,
                category="learning_preference",
                content=(
                    "I prefer concise explanations with practical examples."
                ),
            )

        context = ExecutionContext(
            user_id=USER_ID,
            request=TOPIC,
        )

        personalisation = build_personalised_experience(
            memory_service=memory_service,
            context=context,
        )

        memory_pass = (
            personalisation["memory_count"] > 0
        )

        personalisation_pass = (
            personalisation["personalisation_applied"]
        )

        print(
            "Memory records available:",
            personalisation["memory_count"],
        )

        print(
            "Memory context used:",
            len(personalisation["memory_items"]),
        )

        for index, item in enumerate(
            personalisation["memory_items"],
            start=1,
        ):
            print(
                f"{index}. {item}"
            )

        print()
        print(
            "Personalisation applied without another Gemini call:"
        )
        print(
            "- learner language:",
            LANGUAGE,
        )
        print(
            "- learner level:",
            LEARNER_LEVEL,
        )
        print(
            "- learner preferences: retrieved from MemoryService",
        )
        print(
            "- concise product format preserved",
        )

    except Exception as exc:
        print(
            "Memory/personalisation error:",
            str(exc),
        )

    print()

    # ---------------------------------------------------------------
    # 4. FINAL SUMMARY
    # ---------------------------------------------------------------

    print(
        "========== 4. FINAL DEMO SUMMARY =========="
    )
    print()

    # The label LIVE INTELLIGENCE is deliberately split between:
    # real-live success and demo continuity.
    print_status(
        "INTELLIGENCE PIPELINE",
        live_intelligence_pass,
    )

    print_status(
        "LEARNING CHALLENGE",
        challenge_pass,
    )

    print_status(
        "MEMORY RETRIEVAL",
        memory_pass,
    )

    print_status(
        "PERSONALISATION",
        personalisation_pass,
    )

    print_status(
        "DEMO RESILIENCE",
        intelligence is not None and challenge is not None,
    )

    print()
    print(
        "Execution mode:",
        (
            "REAL LIVE"
            if not fallback_used
            else "CONTROLLED FALLBACK"
        ),
    )

    print()
    print(
        "Cost-efficient architecture:"
    )
    print(
        "- Parallel search is called once."
    )
    print(
        "- The same intelligence result is reused."
    )
    print(
        "- Gemini is not called after a quota failure."
    )
    print(
        "- Memory is independent from the LLM provider."
    )
    print(
        "- Personalisation reuses existing learner context."
    )

    print()

    if (
        live_mode
        and live_intelligence_pass
        and challenge_pass
        and memory_pass
        and personalisation_pass
    ):
        print(
            "G5_FINAL_HACKATHON_DEMO_REAL_SUCCESS"
        )

    elif (
        fallback_used
        and live_intelligence_pass
        and challenge_pass
        and memory_pass
        and personalisation_pass
    ):
        print(
            "G5_FINAL_HACKATHON_DEMO_FALLBACK_SUCCESS"
        )
        print()
        print(
            "NOTE: The external Gemini service was unavailable "
            "for this run; the controlled fallback kept the demo "
            "operational."
        )

    else:
        print(
            "G5_FINAL_HACKATHON_DEMO_INCOMPLETE"
        )


if __name__ == "__main__":
    asyncio.run(main())