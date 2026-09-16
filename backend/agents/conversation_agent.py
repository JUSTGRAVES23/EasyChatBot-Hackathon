"""
Conversation Agent.

Provides character-aware conversational responses
for the EasyChatBot hackathon runtime.

The agent remains provider-independent.

Architecture:

ExecutionContext
|
v
ConversationAgent
|
+--> CharacterProfile
+--> Optional MemoryContext
+--> Optional IntelligenceContext
|
v
ConversationRequest
|
v
LLMService
|
v
LLMProvider
"""

from __future__ import annotations

from agents.agent_manifest import (
    AgentManifest,
)

from agents.agent_result import (
    AgentResult,
)

from agents.base_agent import (
    BaseAgent,
)

from characters.character_profile import (
    CharacterProfile,
)

from conversation.conversation_request import (
    ConversationRequest,
)

from providers.llm.llm_provider import (
    LLMProvider,
)

from runtime.context.execution_context import (
    ExecutionContext,
)

from services.llm_service import (
    LLMService,
)


class ConversationAgent(BaseAgent):
    """
    Character-aware conversation agent.

    The agent consumes the provider-independent
    ExecutionContext.

    Memory and Live Intelligence remain application/runtime
    concerns. The agent only receives their prepared context.
    """

    LIVE_INTELLIGENCE_INSTRUCTION = (
        "When responding using current live intelligence, "
        "create a concise learning brief for the learner. "
        "Do not reproduce articles or provide a long news "
        "summary. Focus only on the most important information. "
        "Keep the main summary between approximately 60 and "
        "100 words. Present no more than three key ideas. "
        "Then briefly explain why the information matters "
        "to the learner. Adapt the language and complexity "
        "to the learner's level and the character's learning "
        "style. Use only information supported by the supplied "
        "live intelligence. Do not invent facts, sources, "
        "statistics, quotations, or URLs. Do not list every "
        "retrieved source in the response. Source metadata is "
        "retained separately by the application."
    )

    def __init__(
        self,
        character: CharacterProfile,
        llm_service: LLMService | None = None,
        llm_provider: LLMProvider | None = None,
    ) -> None:

        super().__init__(
            AgentManifest(
                agent_id="conversation_agent",
                name="Conversation Agent",
                description=(
                    "Provides character-aware "
                    "conversation responses."
                ),
            )
        )

        if (
            llm_service is not None
            and llm_provider is not None
        ):
            raise ValueError(
                "Provide either llm_service or "
                "llm_provider, not both."
            )

        self.character = character

        if llm_service is not None:
            self.llm_service = llm_service

        elif llm_provider is not None:
            self.llm_service = LLMService(
                llm_provider
            )

        else:
            self.llm_service = None

    def build_request(
        self,
        context: ExecutionContext,
    ) -> ConversationRequest:
        """
        Build a provider-independent conversation request.

        Memory and intelligence are explicitly represented
        as contextual information.

        Neither is treated as an instruction.
        """

        system_instruction = (
            f"You are {self.character.name}, "
            f"a character in EasyChatBot. "
            f"Your personality is: "
            f"{self.character.personality} "
            f"Your learning style is: "
            f"{self.character.learning_style} "
            f"Communicate in a way that is consistent "
            f"with this character."
        )

        context_sections: list[str] = []

        # -------------------------------------------------
        # Learner memory
        # -------------------------------------------------

        if context.has_memory_context:
            memory_text = (
                context.memory_context.text
            )

            if memory_text.strip():
                context_sections.append(
                    "Learner memory context:\n"
                    + memory_text
                )

        # -------------------------------------------------
        # Live intelligence
        # -------------------------------------------------

        has_live_intelligence = (
            context.has_intelligence_context
        )

        if has_live_intelligence:
            intelligence_text = (
                context.intelligence_context
                .to_context_text()
            )

            if intelligence_text.strip():
                context_sections.append(
                    "Current live intelligence:\n"
                    + intelligence_text
                )

                context_sections.append(
                    "Live intelligence response rules:\n"
                    + self.LIVE_INTELLIGENCE_INSTRUCTION
                )

        # -------------------------------------------------
        # Combined contextual information
        # -------------------------------------------------

        conversation_context = None

        if context_sections:
            conversation_context = (
                "\n\n".join(
                    context_sections
                )
            )

        # -------------------------------------------------
        # User prompt
        # -------------------------------------------------

        user_prompt = context.request

        if has_live_intelligence:
            user_prompt = (
                "Answer the learner's request using "
                "the supplied current live intelligence. "
                "Prioritize a concise learning experience "
                "over information volume.\n\n"
                "Learner request:\n"
                + context.request
            )

        return ConversationRequest(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            conversation_context=(
                conversation_context
            ),
            character_id=(
                self.character.character_id
            ),
            character_name=(
                self.character.name
            ),
        )

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        """
        Execute the conversation agent.
        """

        conversation_request = (
            self.build_request(context)
        )

        provider_result = None

        if self.llm_service is not None:
            provider_result = (
                await self.llm_service.generate(
                    conversation_request
                )
            )

            if not provider_result.success:
                return AgentResult(
                    success=False,
                    agent_id=(
                        self.manifest.agent_id
                    ),
                    output={
                        "character": (
                            self.character.name
                        ),
                        "character_profile": {
                            "character_id": (
                                self.character.character_id
                            ),
                            "name": (
                                self.character.name
                            ),
                            "description": (
                                self.character.description
                            ),
                            "personality": (
                                self.character.personality
                            ),
                            "learning_style": (
                                self.character.learning_style
                            ),
                        },
                        "personality": (
                            self.character.personality
                        ),
                        "learning_style": (
                            self.character.learning_style
                        ),
                        "message": (
                            "The conversation provider "
                            "could not generate a response."
                        ),
                        "intelligence_context": (
                            conversation_request
                            .conversation_context
                        ),
                        "conversation_request": (
                            conversation_request
                        ),
                        "provider_id": (
                            provider_result.provider_id
                        ),
                        "provider_error": (
                            provider_result.error
                        ),
                    },
                )

        if provider_result is not None:
            message = provider_result.output

        else:
            message = (
                f"{self.character.name}: "
                f"Let's explore this together. "
                f"You asked: "
                f"{context.request}"
            )

        output = {
            "character": (
                self.character.name
            ),
            "character_profile": {
                "character_id": (
                    self.character.character_id
                ),
                "name": (
                    self.character.name
                ),
                "description": (
                    self.character.description
                ),
                "personality": (
                    self.character.personality
                ),
                "learning_style": (
                    self.character.learning_style
                ),
            },
            "personality": (
                self.character.personality
            ),
            "learning_style": (
                self.character.learning_style
            ),
            "message": message,
            "intelligence_context": (
                conversation_request
                .conversation_context
            ),
            "conversation_request": (
                conversation_request
            ),
        }

        if provider_result is not None:
            output["provider_id"] = (
                provider_result.provider_id
            )

        return AgentResult(
            success=True,
            agent_id=(
                self.manifest.agent_id
            ),
            output=output,
        )

