"""
Ollama LLM Provider.

Provides LLM execution through Ollama runtime.

Configuration:

OLLAMA_BASE_URL=http://localhost:11434

OLLAMA_MODEL=gpt-oss:120b-cloud
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

from backend.app.providers.llm.llm_provider import (
    LLMProvider,
)


logger = logging.getLogger(__name__)


class OllamaLLMProvider(LLMProvider):
    """
    Ollama implementation of the LLM provider interface.

    Responsibilities:
    - Send prompts to Ollama
    - Return generated text
    - Keep provider details isolated

    Does NOT:
    - contain business logic
    - manage conversations
    - manage Telegram
    - store memory
    """

    def __init__(self) -> None:

        self.base_url = os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434",
        )

        self.model = os.getenv(
            "OLLAMA_MODEL",
            "gpt-oss:120b-cloud",
        )

        logger.info(
            "Ollama provider initialized. Model=%s",
            self.model,
        )


    async def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
        **kwargs: Any,
    ) -> str:
        """
        Generate a response from Ollama.

        Compatible with ConversationRuntime contract:

        generate(
            system_prompt="...",
            user_message="..."
        )
        """

        if not user_message:

            raise ValueError(
                "User message cannot be empty."
            )


        prompt = f"""
System:
{system_prompt}

User:
{user_message}

Assistant:
"""


        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }


        try:

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300,
            )

            response.raise_for_status()


        except requests.RequestException as exc:

            logger.exception(
                "Ollama request failed."
            )

            raise RuntimeError(
                "Ollama provider unavailable."
            ) from exc


        data = response.json()


        result = data.get(
            "response"
        )


        if not result:

            raise RuntimeError(
                "Ollama returned empty response."
            )


        return result.strip()