"""
LLM Provider Contract.

Defines abstraction for language model providers.

Supported providers:
- OpenAI
- Ollama
- Future enterprise providers

Does NOT:
- Manage conversations.
- Manage users.
- Manage memory.
- Manage LiveKit.
"""


from __future__ import annotations


from abc import ABC, abstractmethod


class LLMProvider(
    ABC
):
    """
    Abstract LLM provider.
    """


    @abstractmethod
    async def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """
        Generate model response.
        """

        raise NotImplementedError