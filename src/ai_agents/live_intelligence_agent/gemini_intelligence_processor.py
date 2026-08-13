"""
Gemini Intelligence Processor.

Implements the provider-independent
IntelligenceProcessor contract.

Responsibilities:

- transform retrieved SearchResult objects
  into concise learner-facing intelligence;
- use the existing LLMProvider abstraction;
- return summary and key information.

Does not:

- perform search;
- access Parallel directly;
- manage runtime state;
- expose provider SDKs.
"""

from __future__ import annotations

import json
from typing import List

from backend.conversation.conversation_request import (
    ConversationRequest,
)

from backend.providers.llm.llm_provider import (
    LLMProvider,
)

from src.ai_agents.live_intelligence_agent.handler import (
    IntelligenceProcessor,
)

from src.providers.search_provider.interface import (
    SearchResult,
)


class GeminiIntelligenceProcessor(
    IntelligenceProcessor,
):
    """
    Gemini implementation of intelligence summarisation.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
    ) -> None:

        if llm_provider is None:
            raise ValueError(
                "llm_provider cannot be None."
            )

        self._llm_provider = llm_provider


    async def summarise(
        self,
        results: List[SearchResult],
        language: str,
        learner_level: str,
    ) -> tuple[str, List[str]]:
        """
        Generate concise grounded intelligence.
        """

        if not results:
            raise ValueError(
                "At least one search result is required."
            )

        sources_text = "\n\n".join(
            [
                (
                    f"SOURCE TITLE: {item.title}\n"
                    f"SOURCE CONTENT:\n{item.content}"
                )
                for item in results[:5]
            ]
        )

        request = ConversationRequest(
            system_instruction=(
                "You are a concise intelligence "
                "summarisation assistant. "
                "Only use information contained in "
                "the supplied sources. "
                "Do not invent facts. "
                "Do not add unsupported claims. "
                "Produce short learner-friendly "
                "information."
            ),
            user_prompt=f"""
Summarise the following retrieved information.

Language:
{language}

Learner level:
{learner_level}

Requirements:

- Write a concise summary of 2-4 sentences.
- Extract exactly 3 key information points.
- Avoid unnecessary details.
- Do not mention that you are an AI.
- Do not repeat source URLs.

Sources:

{sources_text}

Return ONLY valid JSON:

{{
 "summary": "string",
 "key_information": [
    "string",
    "string",
    "string"
 ]
}}
""",
            conversation_context=None,
            character_id="live_intelligence_processor",
            character_name="EasyChatBot Intelligence",
        )

        result = await self._llm_provider.generate(
            request
        )

        if not result.success:
            raise RuntimeError(
                result.error
                or "Gemini summarisation failed."
            )

        raw = str(
            result.output
        ).strip()

        try:
            parsed = json.loads(raw)

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Gemini returned invalid JSON."
            ) from exc


        summary = parsed.get(
            "summary",
            "",
        )

        key_information = parsed.get(
            "key_information",
            [],
        )


        if not isinstance(summary, str):
            raise RuntimeError(
                "Invalid summary returned."
            )

        if not isinstance(
            key_information,
            list,
        ):
            raise RuntimeError(
                "Invalid key information returned."
            )


        return (
            summary.strip(),
            [
                str(item).strip()
                for item in key_information
                if str(item).strip()
            ],
        )
