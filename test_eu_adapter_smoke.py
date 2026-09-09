import asyncio

from google.adk.models import LlmRequest
from google.genai import types

from adk_cinema.agent import root_agent


async def main():
    request = LlmRequest(
        model="gemini-3.7-flash",
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text="Reply with exactly EU_ADAPTER_GEMINI_PASS"
                    )
                ],
            )
        ],
    )

    async for response in root_agent.model.generate_content_async(request):
        if response.content and response.content.parts:
            for part in response.content.parts:
                if part.text:
                    print(part.text)


asyncio.run(main())
