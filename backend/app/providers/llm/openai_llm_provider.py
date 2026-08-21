"""
OpenAI LLM Provider.

Infrastructure implementation of LLM provider.
"""


from __future__ import annotations


import os


from openai import AsyncOpenAI


from app.providers.llm.llm_provider import (
    LLMProvider,
)



class OpenAILLMProvider(
    LLMProvider
):


    def __init__(
        self,
    ):
        api_key = os.getenv(
            "OPENAI_API_KEY"
        )


        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY missing"
            )


        self.client = AsyncOpenAI(
            api_key=api_key
        )



    async def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
    ) -> str:


        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )


        return (
            response
            .choices[0]
            .message
            .content
            or ""
        )