import asyncio
import re

from agents.conversation_agent import ConversationAgent
from characters.character_profile import CharacterProfile
from intelligence.research_service import ResearchService
from providers.llm.llm_provider_factory import LLMProviderFactory
from runtime.context.execution_context import ExecutionContext


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


async def main() -> None:

    query = (
        "What are the most important recent developments "
        "in artificial intelligence?"
    )

    print("========== G3.2 CONCISENESS TEST ==========")

    research_service = ResearchService()

    intelligence_context = await research_service.research(
        user_id="g3-2-conciseness-test",
        query=query,
    )

    if not intelligence_context.has_sources:
        raise RuntimeError(
            "Parallel returned no sources."
        )

    character = CharacterProfile(
        character_id="g3-2-test",
        name="EasyChatBot",
        description=(
            "An AI language-learning assistant that explains "
            "current events clearly."
        ),
        personality=(
            "Friendly, curious, precise, and educational."
        ),
        learning_style=(
            "Explain complex information clearly and "
            "encourage active learning."
        ),
    )

    context = ExecutionContext(
        user_id="g3-2-conciseness-test",
        request=query,
        intelligence_context=intelligence_context,
    )

    provider = LLMProviderFactory.create("gemini")

    agent = ConversationAgent(
        character=character,
        llm_provider=provider,
    )

    result = await agent.execute(context)

    if not result.success:
        raise RuntimeError(
            result.error
            or "Gemini execution failed."
        )

    message = str(
        result.output["message"]
    )

    words = word_count(message)

    print()
    print("========== RESULT ==========")
    print(message)

    print()
    print("========== METRICS ==========")
    print("Word count:", words)
    print(
        "Source count:",
        intelligence_context.source_count,
    )

    print()
    print("========== PRODUCT CHECK ==========")

    if words <= 160:
        print("PASS: response is within maximum product length.")
    else:
        print(
            "FAIL: response exceeds maximum product length."
        )

    if words <= 120:
        print("PASS: response is strongly concise.")
    else:
        print(
            "WARNING: response is above preferred concise range."
        )

    print()
    print("G3.2_CONCISENESS_TEST_COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())

