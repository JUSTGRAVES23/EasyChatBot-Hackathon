"""
Gemini Intelligence Processor.

Transforms Parallel search results into
learner-facing structured intelligence.
"""

from __future__ import annotations

import json
from typing import Any

from conversation.conversation_request import (
    ConversationRequest,
)
from providers.llm.llm_provider import (
    LLMProvider,
)
from src.providers.search_provider.interface import (
    SearchResult,
)


class GeminiIntelligenceProcessor:
    """Gemini-powered intelligence summariser."""

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
                "Return the requested structured output."
            ),
            user_prompt=(
                f"""
Create a concise summary for a {learner_level}
learner in {language}.

Return the requested structured output.

Evidence:

{evidence}
"""
            ),
            conversation_context=None,
            character_id="intelligence_processor",
            character_name="IntelligenceProcessor",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "summary": {
                        "type": "STRING",
                    },
                    "key_information": {
                        "type": "ARRAY",
                        "items": {
                            "type": "STRING",
                        },
                    },
                },
                "required": [
                    "summary",
                    "key_information",
                ],
            },
        )

        result = await self._provider.generate(
            request
        )

        if not result.success:
            raise RuntimeError(
                result.error
                or "Gemini intelligence failed."
            )

        if not isinstance(result.output, str):
            raise RuntimeError(
                "Gemini intelligence returned "
                "no usable structured output."
            )

        output = result.output.strip()

        if not output:
            raise RuntimeError(
                "Gemini intelligence returned "
                "an empty output."
            )

        try:
            data: Any = json.loads(output)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini intelligence returned "
                "invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "Gemini intelligence JSON must "
                "be an object."
            )

        summary = data.get("summary")
        key_information = data.get(
            "key_information"
        )

        if not isinstance(summary, str) or not summary.strip():
            raise RuntimeError(
                "Gemini intelligence JSON must "
                "contain a non-empty string "
                "'summary'."
            )

        if not isinstance(key_information, list):
            raise RuntimeError(
                "Gemini intelligence JSON must "
                "contain a 'key_information' list."
            )

        if not all(
            isinstance(item, str) and item.strip()
            for item in key_information
        ):
            raise RuntimeError(
                "Gemini intelligence "
                "'key_information' must contain "
                "only non-empty strings."
            )

        return (
            summary.strip(),
            [
                item.strip()
                for item in key_information
            ],
        )

