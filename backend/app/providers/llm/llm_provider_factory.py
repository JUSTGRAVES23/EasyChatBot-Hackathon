"""
LLM Provider Factory.
"""


from __future__ import annotations


import os


from app.providers.llm.llm_provider import (
    LLMProvider,
)


from app.providers.llm.openai_llm_provider import (
    OpenAILLMProvider,
)



class LLMProviderFactory:


    @staticmethod
    def create() -> LLMProvider:

        provider = os.getenv(
            "LLM_PROVIDER",
            "openai",
        )


        if provider == "openai":
            return OpenAILLMProvider()


        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )