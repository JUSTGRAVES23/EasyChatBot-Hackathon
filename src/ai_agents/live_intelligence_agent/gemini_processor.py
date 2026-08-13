"""
Gemini Intelligence Processor.

Transforms Parallel search results into
learner-facing structured intelligence.

Architecture:

ParallelSearchProvider
        |
        v
SearchResult[]
        |
        v
GeminiIntelligenceProcessor
        |
        v
(summary, key_information)

Responsibilities:
- summarise retrieved evidence
- create concise learner content
- preserve provider independence

Does not:
- search
- call Parallel
- manage memory
- create challenges
"""

from __future__ import annotations

import json

from backend.conversation.conversation_request import (
    ConversationRequest,
)

from backend.providers.llm.llm_provider import (
    LLMProvider,
)

from src.providers.search_provider.interface import (
    SearchResult,
)


class GeminiIntelligenceProcessor:
    """
    Gemini-powered intelligence summariser.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
    ) -> None:

        if llm_provider is None:
            raise ValueError(
                "LLM provider required."
            )

        self._provider = llm_provider


    async def summarise(
        self,
        results: list[SearchResult],
        language: str,
        learner_level: str,
    ) -> tuple[str, list[str]]:

        if not results:
            raise ValueError(
                "Search results cannot be empty."
            )

        evidence = "\n\n".join(
            [
                f"TITLE: {item.title}\n"
                f"CONTENT: {item.content}"
                for item in results
            ]
        )

        request = ConversationRequest(
            system_instruction=(
                "You are an intelligence analyst. "
                "Summarise only the provided evidence. "
                "Return valid JSON."
            ),

            user_prompt=(
                f"""
Create a concise summary for a {learner_level}
learner in {language}.

Return JSON:

{{
 "summary": "...",
 "key_information": [
    "...",
    "...",
    "..."
 ]
}}

Evidence:

{evidence}
"""
            ),

            conversation_context=None,
            character_id="intelligence_processor",
            character_name="IntelligenceProcessor",
        )

        result = await self._provider.generate(
            request
        )

        if not result.success:
            raise RuntimeError(
                result.error
                or "Gemini intelligence failed."
            )

        data = json.loads(
            result.output
        )

        return (
            data["summary"],
            data["key_information"],
        )