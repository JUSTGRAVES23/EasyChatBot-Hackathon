import asyncio

from conversation.conversation_request import ConversationRequest
from providers.llm.llm_provider_factory import LLMProviderFactory


async def main() -> None:
    provider = LLMProviderFactory.create("gemini")

    request = ConversationRequest(
        system_instruction=(
            "You are EasyChatBot. "
            "Respond concisely."
        ),
        user_prompt=(
            "Reply with exactly: "
            "EASYCHATBOT_FACTORY_GEMINI_OK"
        ),
        conversation_context=None,
        character_id="",
        character_name="",
    )

    result = await provider.generate(request)

    print("success:", result.success)
    print("provider_id:", result.provider_id)
    print("provider_type:", type(provider).__name__)
    print("model:", provider.model)
    print("output:", result.output)
    print("error:", result.error)


if __name__ == "__main__":
    asyncio.run(main())

