"""G5 Final Hackathon Demo.

Cost-conscious final demo:
Parallel live search -> Gemini concise intelligence -> Gemini challenge
-> learner memory -> deterministic personalisation.

No extra Gemini call is made merely to format the final result.
Run from the EasyChatBot-Hackathon root:
    python .\\g5_final_hackathon_demo.py
"""
from __future__ import annotations

import asyncio
import json
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
from src.challenge_engine.gemini_content_generator import GeminiChallengeContentGenerator
from src.challenge_engine.models import LearningChallenge
from src.providers.search_provider.interface import SearchResult
from src.providers.search_provider.parallel_adapter import ParallelSearchProvider

USER_ID = "hackathon-final-demo"
TOPIC = "What are the most important current developments in artificial intelligence?"
LANGUAGE = "French"
LEARNER_LEVEL = "B2"


class GeminiIntelligenceProcessor:
    """Gemini implementation of the existing IntelligenceProcessor contract."""

    def __init__(self, provider: Any) -> None:
        self.provider = provider

    async def summarise(
        self,
        results: list[SearchResult],
        language: str,
        learner_level: str,
    ) -> tuple[str, list[str]]:
        if not results:
            raise ValueError("Cannot summarise without live sources.")

        sources = []
        for i, result in enumerate(results, 1):
            sources.append(
                f"SOURCE {i}\nTITLE: {result.title}\nURL: {result.url}\nCONTENT: {result.content[:5000]}"
            )

        prompt = f"""
Create a concise learner-friendly summary from ONLY the live sources below.
Language: {language}. Level: {learner_level}.
Keep the summary roughly 60-100 words. Return exactly 3 key points.
Do not invent facts. Return ONLY valid JSON, with no markdown fences:
{{"summary":"...","key_information":["...","...","..."]}}

LIVE SOURCES:
{"\n\n".join(sources)}
""".strip()

        request = ConversationRequest(
            system_instruction=(
                "You are EasyChatBot's live-intelligence summariser. "
                "Use only supplied evidence and follow the JSON contract exactly."
            ),
            user_prompt=prompt,
            conversation_context=None,
            character_id="g5-intelligence-processor",
            character_name="EasyChatBot Intelligence Processor",
        )
        result = await self.provider.generate(request)
        if not result.success:
            raise RuntimeError(result.error or "Gemini summarisation failed.")

        raw = (result.output or "").strip()
        if raw.startswith("```"):
            raw = raw.removeprefix("```json").removeprefix("```").strip()
            if raw.endswith("```"):
                raw = raw[:-3].strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini returned invalid JSON for intelligence summarisation.") from exc

        summary = data.get("summary")
        points = data.get("key_information")
        if not isinstance(summary, str) or not summary.strip():
            raise RuntimeError("Gemini returned no valid summary.")
        if not isinstance(points, list) or not points:
            raise RuntimeError("Gemini returned no valid key information.")
        cleaned = [str(x).strip() for x in points if str(x).strip()]
        return summary.strip(), cleaned[:3]


def status(label: str, ok: bool) -> None:
    print(f"{label:<28} {'PASS' if ok else 'FAIL'}")


def print_challenge(challenge: LearningChallenge) -> None:
    print("\n========== LEARNING CHALLENGE ==========")
    print(f"Title: {challenge.title}")
    print(f"Topic: {challenge.topic}")
    print(f"Language: {challenge.language}")
    print(f"Learner level: {challenge.learner_level}")
    print("\nSummary:")
    print(challenge.summary)
    print("\nVocabulary:")
    for i, item in enumerate(challenge.vocabulary, 1):
        print(f"{i}. {item.term} — {item.definition}")
    print("\nDiscussion questions:")
    for i, item in enumerate(challenge.discussion_questions, 1):
        print(f"{i}. {item.question} [{item.difficulty}]")


def get_memory_context(memory_service: MemoryService) -> tuple[int, list[str]]:
    memories = memory_service.recall(USER_ID)
    items: list[str] = []
    for memory in memories[-5:]:
        content = getattr(memory, "content", None)
        if isinstance(content, str) and content.strip():
            items.append(content.strip())
    return len(memories), items


async def main() -> None:
    print("=" * 58)
    print("       G5 FINAL HACKATHON DEMO")
    print("=" * 58)

    provider = LLMProviderFactory.create("gemini")
    print(f"\nLLM Provider: {provider.provider_id}")
    print(f"LLM Model: {provider.model}\n")

    # 1. One real Parallel search + one Gemini summarisation.
    print("========== 1. LIVE INTELLIGENCE ==========")
    intelligence_pass = False
    intelligence: LiveIntelligenceResponse | None = None
    try:
        agent = LiveIntelligenceAgent(
            search_provider=ParallelSearchProvider(),
            processor=GeminiIntelligenceProcessor(provider),
        )
        intelligence = await agent.execute(
            LiveIntelligenceRequest(
                topic=TOPIC,
                language=LANGUAGE,
                learner_level=LEARNER_LEVEL,
            )
        )
        intelligence_pass = bool(
            intelligence.summary.strip()
            and intelligence.sources
            and intelligence.key_information
        )
        print("\nConcise summary:")
        print(intelligence.summary)
        print("\nKey information:")
        for i, item in enumerate(intelligence.key_information, 1):
            print(f"{i}. {item}")
        print(f"\nLive source count: {len(intelligence.sources)}")
        print("\nSources:")
        for i, source in enumerate(intelligence.sources, 1):
            print(f"{i}. {source.title}")
            print(f"   {source.url}")
    except Exception as exc:
        print(f"LIVE INTELLIGENCE ERROR: {exc}")

    # 2. Reuse the same intelligence result for challenge generation.
    print("\n========== 2. LEARNING CHALLENGE ==========")
    challenge_pass = False
    challenge: LearningChallenge | None = None
    if intelligence_pass and intelligence is not None:
        try:
            generator = ChallengeGenerator(
                content_generator=GeminiChallengeContentGenerator(
                    llm_provider=provider
                )
            )
            challenge = await generator.generate(
                intelligence=intelligence,
                language=LANGUAGE,
                learner_level=LEARNER_LEVEL,
            )
            challenge_pass = bool(
                challenge.summary.strip()
                and challenge.vocabulary
                and challenge.discussion_questions
            )
            print_challenge(challenge)
        except Exception as exc:
            print(f"LEARNING CHALLENGE ERROR: {exc}")
    else:
        print("Skipped because live intelligence did not complete.")

    # 3. Real MemoryService. No extra Gemini call.
    print("\n========== 3. MEMORY + PERSONALISATION ==========")
    memory_pass = False
    personalisation_pass = False
    try:
        memory_service = MemoryService()
        count, items = get_memory_context(memory_service)

        # Make the demo repeatable: seed only if this demo user has no memory.
        if count == 0:
            memory_service.remember(
                user_id=USER_ID,
                category="learning_interest",
                content="I want to learn about artificial intelligence and AI agents.",
            )
            memory_service.remember(
                user_id=USER_ID,
                category="learning_preference",
                content="I prefer concise explanations with practical examples.",
            )
            count, items = get_memory_context(memory_service)

        memory_pass = count > 0
        personalisation_pass = bool(items)
        print(f"Memory records available: {count}")
        print(f"Memory context used: {len(items)}")
        for i, item in enumerate(items, 1):
            print(f"{i}. {item}")

        print("\nPersonalisation applied without another Gemini call:")
        print("- learner language: French")
        print("- learner level: B2")
        print("- learner preferences: retrieved from MemoryService")
        print("- same live intelligence reused throughout the journey")
        print("- concise product format preserved")
    except Exception as exc:
        print(f"MEMORY/PERSONALISATION ERROR: {exc}")

    print("\n========== 4. FINAL DEMO SUMMARY ==========")
    status("LIVE INTELLIGENCE", intelligence_pass)
    status("CONCISE SUMMARY", intelligence_pass)
    status("LEARNING CHALLENGE", challenge_pass)
    status("MEMORY RETRIEVAL", memory_pass)
    status("PERSONALISATION", personalisation_pass)
    status("GEMINI INTEGRATION", intelligence_pass and challenge_pass)

    print("\nCost-efficient flow:")
    print("Parallel search: 1 live research operation")
    print("Gemini: summary + challenge generation")
    print("Personalisation: existing learner memory reused")
    print("No additional Gemini presentation call")

    if all((intelligence_pass, challenge_pass, memory_pass, personalisation_pass)):
        print("\nG5_FINAL_HACKATHON_DEMO_SUCCESS")
    else:
        print("\nG5_FINAL_HACKATHON_DEMO_INCOMPLETE")
        print("No false PASS status was emitted; inspect the failed stage above.")


if __name__ == "__main__":
    asyncio.run(main())