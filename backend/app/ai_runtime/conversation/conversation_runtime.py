"""
Conversation Runtime.

Coordinates AI responses.

Does NOT:
- Call vendors directly.
- Manage LiveKit.
- Store conversations.
"""


from __future__ import annotations


from dataclasses import dataclass


from app.providers.llm.llm_provider import (
    LLMProvider,
)



@dataclass(
    frozen=True,
    slots=True,
)
class ConversationRuntime:


    llm_provider: LLMProvider



    async def respond(
        self,
        *,
        character_instruction: str,
        learner_message: str,
    ) -> str:


        return await self.llm_provider.generate(
            system_prompt=character_instruction,
            user_message=learner_message,
        )