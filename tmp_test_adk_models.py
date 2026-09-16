import asyncio
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

async def test(model: str) -> None:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents="Reply with exactly: ADK MODEL TEST PASS",
        )

        print(f"{model}: PASS")
        print(response.text)

    except Exception as exc:
        print(f"{model}: FAIL")
        print(type(exc).__name__)
        print(exc)

async def main() -> None:
    for model in [
        "gemini-3.5-flash",
        "gemini-3.7-flash",
        "gemini-3.8-flash",
    ]:
        await test(model)

if __name__ == "__main__":
    asyncio.run(main())
