"""
Gemini Challenge Content Generator.

Provider adapter for the provider-independent
ChallengeContentGenerator contract.

The Challenge Engine remains independent from
specific LLM providers.

Architecture:

ChallengeGenerator
        |
        v
GeminiChallengeContentGenerator
        |
        v
ConversationRequest
        |
        v
LLMProvider
        |
        v
GeminiProvider
        |
        v
Gemini API

Cost design:

- Vocabulary and questions are generated through ONE
  Gemini request.
- The generated JSON is cached for the lifetime of
  this content-generator instance.
- No second Gemini request is made when the
  ChallengeGenerator subsequently requests questions.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from conversation.conversation_request import (
    ConversationRequest,
)

from providers.llm.llm_provider import (
    LLMProvider,
)

from src.challenge_engine.models import (
    DiscussionQuestion,
    VocabularyItem,
)


class GeminiChallengeContentGenerator:
    """
    Gemini-backed implementation of the
    ChallengeContentGenerator protocol.

    The class does not depend directly on the Gemini SDK.
    It receives the provider-independent LLMProvider
    abstraction through dependency injection.
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

        self._generated_content: dict[str, Any] | None = None

        self._generation_lock = asyncio.Lock()

    async def generate_vocabulary(
        self,
        summary: str,
        language: str,
        learner_level: str,
    ) -> list[VocabularyItem]:
        """
        Generate vocabulary from the supplied summary.

        The first generation request produces both vocabulary
        and discussion questions.

        The generated result is cached so that the subsequent
        question-generation call does not trigger another
        Gemini API request.
        """

        content = await self._ensure_generated(
            summary=summary,
            language=language,
            learner_level=learner_level,
        )

        vocabulary = content.get(
            "vocabulary",
            [],
        )

        if not isinstance(
            vocabulary,
            list,
        ):
            raise RuntimeError(
                "Gemini vocabulary output must be a list."
            )

        result: list[VocabularyItem] = []

        for item in vocabulary:

            if not isinstance(
                item,
                dict,
            ):
                continue

            term = str(
                item.get(
                    "term",
                    "",
                )
            ).strip()

            definition = str(
                item.get(
                    "definition",
                    "",
                )
            ).strip()

            example_value = item.get(
                "example"
            )

            example = None

            if example_value is not None:
                example = str(
                    example_value
                ).strip()

            if not term or not definition:
                continue

            result.append(
                VocabularyItem(
                    term=term,
                    definition=definition,
                    example=example,
                )
            )

        return result

    async def generate_questions(
        self,
        summary: str,
        language: str,
        learner_level: str,
    ) -> list[DiscussionQuestion]:
        """
        Generate discussion questions from the supplied summary.

        Uses the cached result of the shared Gemini generation
        whenever generate_vocabulary() has already executed.
        """

        content = await self._ensure_generated(
            summary=summary,
            language=language,
            learner_level=learner_level,
        )

        questions = content.get(
            "questions",
            [],
        )

        if not isinstance(
            questions,
            list,
        ):
            raise RuntimeError(
                "Gemini questions output must be a list."
            )

        result: list[DiscussionQuestion] = []

        for item in questions:

            if not isinstance(
                item,
                dict,
            ):
                continue

            question = str(
                item.get(
                    "question",
                    "",
                )
            ).strip()

            difficulty = str(
                item.get(
                    "difficulty",
                    learner_level,
                )
            ).strip()

            if not question:
                continue

            result.append(
                DiscussionQuestion(
                    question=question,
                    difficulty=(
                        difficulty
                        or learner_level
                    ),
                )
            )

        return result

    async def _ensure_generated(
        self,
        summary: str,
        language: str,
        learner_level: str,
    ) -> dict[str, Any]:
        """
        Execute exactly one Gemini generation request.

        The resulting structured JSON is cached and reused by
        both ChallengeContentGenerator methods.
        """

        if not isinstance(
            summary,
            str,
        ) or not summary.strip():
            raise ValueError(
                "Challenge summary cannot be empty."
            )

        if not isinstance(
            language,
            str,
        ) or not language.strip():
            raise ValueError(
                "Challenge language cannot be empty."
            )

        if not isinstance(
            learner_level,
            str,
        ) or not learner_level.strip():
            raise ValueError(
                "Learner level cannot be empty."
            )

        async with self._generation_lock:

            if self._generated_content is not None:
                return self._generated_content

            system_instruction = (
                "You are an educational content generator "
                "for EasyChatBot. "
                "Generate concise language-learning content "
                "from the supplied live-information summary. "
                "Use only information supported by the summary. "
                "Do not invent facts, statistics, sources, URLs, "
                "quotations, or claims. "
                "Adapt the content to the learner's language "
                "and level. "
                "Return only valid JSON matching the requested "
                "schema."
            )

            user_prompt = f"""
Create learning content from this live-information summary.

Language:
{language}

Learner level:
{learner_level}

Summary:
{summary}

Generate:

- exactly 3 relevant vocabulary items;
- exactly 2 discussion questions.

Vocabulary requirements:
- term must be relevant to the summary;
- definition must be appropriate for the learner level;
- example must be short and natural;
- do not introduce unsupported information.

Question requirements:
- questions must test understanding of the summary;
- questions should encourage explanation or reflection;
- questions must be appropriate for the learner level;
- do not introduce unsupported information.

Return ONLY valid JSON.

Required structure:

{{
  "vocabulary": [
    {{
      "term": "string",
      "definition": "string",
      "example": "string"
    }}
  ],
  "questions": [
    {{
      "question": "string",
      "difficulty": "{learner_level}"
    }}
  ]
}}
""".strip()

            request = ConversationRequest(
                system_instruction=(
                    system_instruction
                ),
                user_prompt=user_prompt,
                conversation_context=None,
                character_id="challenge_engine",
                character_name="EasyChatBot",
            )

            provider_result = (
                await self._llm_provider.generate(
                    request
                )
            )

            if provider_result is None:
                raise RuntimeError(
                    "LLM provider returned no result."
                )

            if not provider_result.success:
                raise RuntimeError(
                    provider_result.error
                    or "Gemini challenge generation failed."
                )

            raw_output = str(
                provider_result.output
                or ""
            ).strip()

            if not raw_output:
                raise RuntimeError(
                    "Gemini returned empty challenge content."
                )

            parsed = (
                self._parse_json_output(
                    raw_output
                )
            )

            self._validate_generated_content(
                parsed
            )

            self._generated_content = parsed

            return parsed

    @staticmethod
    def _parse_json_output(
        raw_output: str,
    ) -> dict[str, Any]:
        """
        Parse Gemini JSON output.

        Handles the normal JSON response as well as a
        fenced JSON block if the model returns one.
        """

        candidate = raw_output.strip()

        if candidate.startswith(
            "```"
        ):
            lines = candidate.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            candidate = "\n".join(
                lines
            ).strip()

        try:
            parsed = json.loads(
                candidate
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini challenge output was not valid JSON."
            ) from exc

        if not isinstance(
            parsed,
            dict,
        ):
            raise RuntimeError(
                "Gemini challenge output must be a JSON object."
            )

        return parsed

    @staticmethod
    def _validate_generated_content(
        content: dict[str, Any],
    ) -> None:
        """
        Validate the minimum structural contract.

        This is deliberately deterministic and does not
        make another LLM call.
        """

        vocabulary = content.get(
            "vocabulary"
        )

        questions = content.get(
            "questions"
        )

        if not isinstance(
            vocabulary,
            list,
        ):
            raise RuntimeError(
                "Gemini vocabulary output must be a list."
            )

        if not isinstance(
            questions,
            list,
        ):
            raise RuntimeError(
                "Gemini questions output must be a list."
            )

        if not vocabulary:
            raise RuntimeError(
                "Gemini generated no vocabulary items."
            )

        if not questions:
            raise RuntimeError(
                "Gemini generated no discussion questions."
            )

        for item in vocabulary:
            if not isinstance(
                item,
                dict,
            ):
                raise RuntimeError(
                    "Invalid vocabulary item generated by Gemini."
                )

            if not str(
                item.get(
                    "term",
                    "",
                )
            ).strip():
                raise RuntimeError(
                    "Gemini generated a vocabulary item "
                    "without a term."
                )

            if not str(
                item.get(
                    "definition",
                    "",
                )
            ).strip():
                raise RuntimeError(
                    "Gemini generated a vocabulary item "
                    "without a definition."
                )

        for item in questions:
            if not isinstance(
                item,
                dict,
            ):
                raise RuntimeError(
                    "Invalid discussion question generated "
                    "by Gemini."
                )

            if not str(
                item.get(
                    "question",
                    "",
                )
            ).strip():
                raise RuntimeError(
                    "Gemini generated an empty discussion question."
                )

