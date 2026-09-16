import asyncio
import os

from dotenv import load_dotenv

from providers.parallel.parallel_client import ParallelClientWrapper


load_dotenv()


async def main():
    print("PARALLEL KEY:", "SET" if os.getenv("PARALLEL_API_KEY") else "MISSING")

    client = ParallelClientWrapper()

    print("Calling Parallel...")
    print("Timeout: 45 seconds")

    result = await asyncio.wait_for(
        client.search(
            "current artificial intelligence developments 2026"
        ),
        timeout=45,
    )

    print("Parallel returned:", type(result))
    print(
        "Result keys:",
        result.keys() if isinstance(result, dict) else "N/A",
    )
    print("SUCCESS")


if __name__ == "__main__":
    asyncio.run(main())

