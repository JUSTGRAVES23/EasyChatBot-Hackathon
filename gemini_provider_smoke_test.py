import asyncio

# Import the authoritative LLM configuration first.
# This loads the project-root .env file.
from backend.providers.llm.config import get_gemini_model

from backend.conversation.conversation_request import ConversationRequest
from backend.providers.llm.gemini_provider import GeminiProvider


async def main() -> None:
    model = get_gemini_model()

    request = ConversationRequest(
        system_instruction=(
            "You are EasyChatBot. "
            "Respond concisely."
        ),
        user_prompt=(
            "Reply with exactly: "
            "EASYCHATBOT_GEMINI_PROVIDER_OK"
        ),
        conversation_context=None,
        character_id="",
        character_name="",
    )

    provider = GeminiProvider(
        model=model,
    )

    result = await provider.generate(
        request
    )

    print("success:", result.success)
    print("provider_id:", result.provider_id)
    print("model:", model)
    print("output:", result.output)
    print("error:", result.error)


if __name__ == "__main__":
    asyncio.run(main())
