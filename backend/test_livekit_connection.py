import asyncio
import os

from dotenv import load_dotenv
from livekit import api


load_dotenv()


async def main():

    print(
        "URL:",
        os.getenv("LIVEKIT_URL")
    )

    print(
        "KEY:",
        os.getenv("LIVEKIT_API_KEY")[:5]
        if os.getenv("LIVEKIT_API_KEY")
        else "MISSING"
    )

    print(
        "SECRET LENGTH:",
        len(
            os.getenv(
                "LIVEKIT_API_SECRET",
                ""
            )
        )
    )

    client = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    print("CLIENT CREATED")

    await client.aclose()


asyncio.run(main())