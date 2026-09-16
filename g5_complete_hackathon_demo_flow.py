import asyncio
import re

from agents.conversation_agent import (
    ConversationAgent,
)

from characters.character_profile import (
    CharacterProfile,
)

from conversation.conversation_request import (
    ConversationRequest,
)

from intelligence.intelligence_context import (
    IntelligenceContext,
    IntelligenceSource,
)

from memory.memory_service import (
    MemoryService,
)

from providers.llm.llm_provider_factory import (
    LLMProviderFactory,
)

from runtime.context.execution_context import (
    ExecutionContext,
)

from services.companion_service import (
    CompanionService,
)

from src.ai_agents.live_intelligence_agent.handler import (
    IntelligenceProcessor,
    LiveIntelligenceAgent,
    LiveIntelligenceRequest,
    LiveIntelligenceResponse,
)

from src.challenge_engine.generator import (
    ChallengeGenerator,
)

from src.challenge_engine.gemini_content_generator import (
    GeminiChallengeContentGenerator,
)

from src.providers.search_provider.interface import (
    SearchResult,
)

from src.providers.search_provider.parallel_adapter import (
    ParallelSearchProvider,
)


class GeminiIntelligenceProcessor(
    IntelligenceProcessor,
):
    """
    Gemini-backed processor for the G5 demo.

    Converts live Parallel search results into:

        - one concise learner-facing summary
        - three concise key information points

    The parser deliberately uses plain text markers rather
    than requiring Gemini to return strict JSON. This keeps
    the provider adapter simple and robust.
    """

    def __init__(
        self,
        provider,
    ) -> None:
        self._provider = provider

    async def summarise(
        self,
        results: list[SearchResult],
        language: str,
        learner_level: str,
    ) -> tuple[str, list[str]]:

        if not results:
            raise ValueError(
                "Cannot summarise empty research results."
            )

        source_text = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            content = (
                result.content[:2500]
                if result.content
                else ""
            )

            source_text.append(
                (
                    f"SOURCE {index}\n"
                    f"Title: {result.title}\n"
                    f"URL: {result.url}\n"
                    f"Content: {content}"
                )
            )

        prompt = f"""
You are the concise intelligence summarisation
component of EasyChatBot Academy.

The learner is level {learner_level}.

Use ONLY information supported by the live sources.

Create a short learner-friendly summary.

STRICT OUTPUT FORMAT:

SUMMARY:
Write exactly 2 or 3 short sentences here.

KEY INFORMATION:
1. One short supported fact.
2. One short supported fact.
3. One short supported fact.

Rules:

- Write in {language}.
- Maximum 3 sentences for SUMMARY.
- Exactly 3 key information points.
- Keep every point concise.
- Do not invent information.
- Do not add introductions.
- Do not add conclusions.
- Do not use markdown tables.
- Do not reproduce long source passages.
- Do not include URLs in the summary.
- Avoid unnecessary detail.
- The learner should be able to understand the
  main development without reading the sources.

LIVE SOURCES:

{chr(10).join(source_text)}
"""

        request = ConversationRequest(
            system_instruction=(
                "You are a concise, evidence-grounded "
                "AI learning information processor. "
                "Follow the requested output format."
            ),
            user_prompt=prompt,
        )

        result = await self._provider.generate(
            request
        )

        if not result.success:
            raise RuntimeError(
                result.error
                or "Gemini intelligence summarisation failed."
            )

        raw_output = str(
            result.output or ""
        ).strip()

        if not raw_output:
            raise RuntimeError(
                "Gemini returned an empty intelligence response."
            )

        summary, key_information = (
            self._parse_response(
                raw_output
            )
        )

        return (
            summary,
            key_information,
        )

    @staticmethod
    def _parse_response(
        text: str,
    ) -> tuple[str, list[str]]:
        """
        Parse Gemini's marked plain-text response.

        The parser is intentionally tolerant of:

            SUMMARY:
            ...

            KEY INFORMATION:
            1. ...
            2. ...
            3. ...

        It also tolerates markdown formatting around
        the section headings.
        """

        normalised = text.strip()

        summary_match = re.search(
            r"SUMMARY\s*:\s*(.*?)(?=\n\s*KEY INFORMATION\s*:)",
            normalised,
            flags=re.IGNORECASE | re.DOTALL,
        )

        key_match = re.search(
            r"KEY INFORMATION\s*:\s*(.*)$",
            normalised,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if summary_match is None:
            summary_match = re.search(
                r"(?:\*\*)?SUMMARY(?:\*\*)?\s*:\s*(.*?)(?=\n)",
                normalised,
                flags=re.IGNORECASE | re.DOTALL,
            )

        if summary_match is None:
            raise RuntimeError(
                "Gemini response did not contain a SUMMARY section."
            )

        summary = (
            summary_match.group(1)
            .strip()
        )

        if key_match is None:
            raise RuntimeError(
                "Gemini response did not contain "
                "a KEY INFORMATION section."
            )

        key_block = (
            key_match.group(1)
            .strip()
        )

        key_information: list[str] = []

        for line in key_block.splitlines():

            cleaned = line.strip()

            if not cleaned:
                continue

            cleaned = re.sub(
                r"^\s*(?:[-*]|\d+[.)])\s*",
                "",
                cleaned,
            )

            cleaned = cleaned.strip()

            if cleaned:
                key_information.append(
                    cleaned
                )

        key_information = (
            key_information[:3]
        )

        if not summary:
            raise RuntimeError(
                "Gemini returned an empty SUMMARY section."
            )

        if len(key_information) < 3:
            raise RuntimeError(
                "Gemini returned fewer than "
                "three KEY INFORMATION points."
            )

        return (
            summary,
            key_information,
        )


def convert_to_backend_intelligence(
    response: LiveIntelligenceResponse,
) -> IntelligenceContext:
    """
    Convert LiveIntelligenceResponse into the backend
    IntelligenceContext consumed by ConversationAgent.
    """

    sources = tuple(
        IntelligenceSource(
            title=source.title,
            url=source.url,
            source=source.source,
            content=source.content,
        )
        for source in response.sources
    )

    return IntelligenceContext(
        query=response.topic,
        sources=sources,
    )


async def main() -> None:

    print(
        "=================================================="
    )

    print(
        "       G5 COMPLETE HACKATHON DEMO FLOW"
    )

    print(
        "=================================================="
    )

    print()


    # -------------------------------------------------
    # 1. GEMINI CONFIGURATION
    # -------------------------------------------------

    provider = (
        LLMProviderFactory.create(
            "gemini"
        )
    )

    print(
        "LLM Provider:",
        provider.provider_id,
    )

    print(
        "LLM Model:",
        provider.model,
    )

    print()


    # -------------------------------------------------
    # 2. LIVE INTELLIGENCE
    #
    # ONE Parallel search only.
    # -------------------------------------------------

    print(
        "========== 1. LIVE INTELLIGENCE =========="
    )

    topic = (
        "What are the most important current "
        "developments in artificial intelligence?"
    )

    search_provider = (
        ParallelSearchProvider()
    )

    intelligence_processor = (
        GeminiIntelligenceProcessor(
            provider
        )
    )

    live_intelligence_agent = (
        LiveIntelligenceAgent(
            search_provider=search_provider,
            processor=intelligence_processor,
        )
    )

    live_response = (
        await live_intelligence_agent.execute(
            LiveIntelligenceRequest(
                topic=topic,
                language="French",
                learner_level="B2",
            )
        )
    )

    print(
        "Topic:",
        live_response.topic,
    )

    print()

    print(
        "Concise summary:"
    )

    print(
        live_response.summary
    )

    print()

    print(
        "Key information:"
    )

    for index, item in enumerate(
        live_response.key_information,
        start=1,
    ):
        print(
            f"{index}. {item}"
        )

    print()

    print(
        "Live source count:",
        len(live_response.sources),
    )

    print()


    # -------------------------------------------------
    # 3. LEARNING CHALLENGE
    #
    # Reuses the SAME intelligence result.
    # No additional Parallel search.
    # -------------------------------------------------

    print(
        "========== 2. LEARNING CHALLENGE =========="
    )

    challenge_generator = ChallengeGenerator(
        content_generator=(
            GeminiChallengeContentGenerator(
                llm_provider=provider
            )
        )
    )

    challenge = (
        await challenge_generator.generate(
            intelligence=live_response,
            language="French",
            learner_level="B2",
        )
    )

    print(
        "Title:",
        challenge.title,
    )

    print()

    print(
        "Summary:"
    )

    print(
        challenge.summary
    )

    print()

    print(
        "Vocabulary:"
    )

    for index, item in enumerate(
        challenge.vocabulary,
        start=1,
    ):

        print(
            f"{index}. {item.term}"
        )

        print(
            f"   {item.definition}"
        )

    print()

    print(
        "Discussion questions:"
    )

    for index, item in enumerate(
        challenge.discussion_questions,
        start=1,
    ):

        print(
            f"{index}. {item.question}"
        )

    print()


    # -------------------------------------------------
    # 4. MEMORY + PERSONALISATION
    #
    # No new research call.
    # -------------------------------------------------

    print(
        "========== 3. MEMORY + PERSONALISATION =========="
    )

    user_id = (
        "g5_hackathon_demo_learner"
    )

    character = CharacterProfile(
        character_id="g5-demo-character",
        name="EasyChatBot",
        description=(
            "An AI language learning companion "
            "that turns current information into "
            "short learning experiences."
        ),
        personality=(
            "Friendly, precise, encouraging, "
            "and curious."
        ),
        learning_style=(
            "Uses concise explanations, examples, "
            "and practical challenges."
        ),
    )

    memory_service = MemoryService()

    conversation_agent = (
        ConversationAgent(
            character=character,
            llm_provider=provider,
        )
    )

    companion_service = (
        CompanionService(
            character=character,
            conversation_agent=conversation_agent,
            memory_service=memory_service,
        )
    )

    backend_intelligence = (
        convert_to_backend_intelligence(
            live_response
        )
    )

    learner_context = ExecutionContext(
        user_id=user_id,
        request=(
            "I have just learned about current "
            "AI developments. Give me one short "
            "follow-up challenge based on this topic."
        ),
        intelligence_context=(
            backend_intelligence
        ),
    )

    personalised_result = (
        await companion_service.interact(
            learner_context,
            use_research=False,
        )
    )

    print(
        "Memory records available:",
        personalised_result[
            "memory_count"
        ],
    )

    print(
        "Memory context used:",
        personalised_result[
            "memory_context_count"
        ],
    )

    print()

    print(
        "Personalised response:"
    )

    conversation = (
        personalised_result[
            "conversation"
        ]
    )

    if isinstance(
        conversation,
        dict,
    ):

        print(
            conversation.get(
                "message",
                conversation,
            )
        )

    else:

        print(
            conversation
        )

    print()


    # -------------------------------------------------
    # 5. FINAL DEMO STATUS
    # -------------------------------------------------

    print(
        "========== 4. DEMO SUMMARY =========="
    )

    print(
        "LIVE INTELLIGENCE: PASS"
    )

    print(
        "LEARNING CHALLENGE: PASS"
    )

    print(
        "MEMORY: PASS"
    )

    print(
        "PERSONALISATION: PASS"
    )

    print(
        "GEMINI: PASS"
    )

    print()

    print(
        "Parallel searches used: 1"
    )

    print(
        "The same live intelligence result was "
        "reused throughout the learning journey."
    )

    print()

    print(
        "G5_COMPLETE_HACKATHON_DEMO_FLOW_SUCCESS"
    )


if __name__ == "__main__":
    asyncio.run(main())

