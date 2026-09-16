import asyncio
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    response = await client.aio.models.list()

    print("Available Gemini models supporting generateContent:")

    for model in response:
        actions = getattr(model, "supported_actions", None)

        if actions is None or "generateContent" in actions:
            print(model.name)

if __name__ == "__main__":
    asyncio.run(main())
