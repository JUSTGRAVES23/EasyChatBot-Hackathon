import pytest

from backend.providers.parallel.parallel_client import (
    ParallelClientWrapper,
)


class FakeSearchResult:

    def model_dump(self):
        return {
            "results": [
                {
                    "title": "Example",
                    "url": "https://example.com",
                }
            ]
        }


class FakeParallelClient:

    def search(
        self,
        *,
        search_queries,
        mode,
        objective,
    ):
        assert len(search_queries) == 1
        assert mode == "advanced"
        assert objective == (
            "Latest artificial intelligence news"
        )

        return FakeSearchResult()


@pytest.mark.asyncio
async def test_parallel_client_normalizes_response():

    wrapper = object.__new__(
        ParallelClientWrapper
    )

    wrapper.api_key = "test-key"

    wrapper._client = FakeParallelClient()

    result = await wrapper.search(
        "Latest artificial intelligence news"
    )

    assert result["query"] == (
        "Latest artificial intelligence news"
    )

    assert result["results"] == {
        "results": [
            {
                "title": "Example",
                "url": "https://example.com",
            }
        ]
    }