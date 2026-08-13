import asyncio

from backend.intelligence.research_service import ResearchService


async def main() -> None:
    service = ResearchService()

    query = (
        "What are the most important developments "
        "in artificial intelligence today?"
    )

    print("query:", query)
    print()
    print("Running real Parallel research...")
    print()

    intelligence = await service.research(
        user_id="hackathon-smoke-test",
        query=query,
    )

    print("research_success: True")
    print("query:", intelligence.query)
    print("source_count:", intelligence.source_count)
    print("has_sources:", intelligence.has_sources)
    print("has_summary:", intelligence.has_summary)
    print()

    for index, source in enumerate(
        intelligence.sources,
        start=1,
    ):
        print(f"--- SOURCE {index} ---")
        print("title:", source.title)
        print("url:", source.url)
        print("source:", source.source)
        print("content:", source.content[:500])
        print()

    print("========== CONTEXT TEXT ==========")
    print(intelligence.to_context_text())


if __name__ == "__main__":
    asyncio.run(main())
