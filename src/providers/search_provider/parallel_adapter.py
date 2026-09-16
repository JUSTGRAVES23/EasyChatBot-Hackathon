"""
Parallel Search Provider Adapter.

Bridges the provider-independent SearchProvider contract
to the existing EasyChatBot ParallelClientWrapper.

Architecture:

Live Intelligence Agent
        |
        v
SearchProvider Interface
        |
        v
ParallelSearchProvider
        |
        v
Existing ParallelClientWrapper
        |
        v
Parallel Search API

The official Parallel SDK remains isolated inside:

    backend/providers/parallel/parallel_client.py

This adapter must not import or instantiate the Parallel SDK
directly.
"""

from typing import Any

from providers.parallel.parallel_client import (
    ParallelClientWrapper,
)

from src.providers.search_provider.interface import (
    SearchProvider,
    SearchResult,
)


class ParallelSearchProvider(SearchProvider):
    """
    SearchProvider implementation backed by the existing
    ParallelClientWrapper.
    """

    def __init__(
        self,
        api_key: str | None = None,
        client: ParallelClientWrapper | None = None,
    ) -> None:
        """
        Initialise the provider.

        Args:
            api_key:
                Optional Parallel API key.

                If omitted, the existing ParallelClientWrapper
                loads PARALLEL_API_KEY from the environment/.env.

            client:
                Optional injected client for testing.
        """

        self._client = client or ParallelClientWrapper(
            api_key=api_key
        )

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        """
        Execute a Parallel search and normalise its results.

        Args:
            query:
                Natural-language research objective.

            max_results:
                Maximum number of results returned.

        Returns:
            Provider-independent SearchResult objects.
        """

        if not query.strip():
            raise ValueError(
                "Search query cannot be empty"
            )

        if max_results <= 0:
            raise ValueError(
                "max_results must be greater than zero"
            )

        response = await self._client.search(
            query=query
        )

        raw_results = self._extract_results(
            response
        )

        normalised_results: list[SearchResult] = []

        for raw_result in raw_results[:max_results]:
            result = self._normalise_result(
                raw_result
            )

            if result is not None:
                normalised_results.append(result)

        return normalised_results

    @staticmethod
    def _extract_results(
        response: Any,
    ) -> list[Any]:
        """
        Extract the actual result collection from the
        ParallelClientWrapper response.

        The existing wrapper returns:

            {
                "query": "...",
                "search_queries": [...],
                "results": <normalised SDK response>
            }

        The SDK response may itself contain:

            {
                "results": [...]
            }

        Therefore this method handles both levels of wrapping.
        """

        if not isinstance(response, dict):
            raise TypeError(
                "Parallel client response must be a dictionary"
            )

        raw_results = response.get(
            "results",
            []
        )

        # The SDK response itself may contain a nested
        # "results" collection.
        if isinstance(raw_results, dict):
            nested_results = raw_results.get(
                "results"
            )

            if isinstance(nested_results, list):
                return nested_results

            # Some SDK versions may expose the result
            # collection under another common field.
            nested_data = raw_results.get(
                "data"
            )

            if isinstance(nested_data, list):
                return nested_data

        if isinstance(raw_results, list):
            return raw_results

        # If the SDK returned an object that was not converted
        # to a dictionary, try to inspect its result attribute.
        nested_results = getattr(
            raw_results,
            "results",
            None,
        )

        if isinstance(nested_results, list):
            return nested_results

        raise TypeError(
            "Parallel search response does not contain "
            "a supported results collection"
        )

    @staticmethod
    def _normalise_result(
        raw_result: Any,
    ) -> SearchResult | None:
        """
        Convert one Parallel result into SearchResult.

        Parallel results may arrive either as dictionaries
        or SDK/Pydantic objects.
        """

        if isinstance(raw_result, dict):
            title = str(
                raw_result.get(
                    "title",
                    ""
                )
            ).strip()

            url = str(
                raw_result.get(
                    "url",
                    ""
                )
            ).strip()

            excerpts = raw_result.get(
                "excerpts",
                []
            )

            # Support providers/SDK versions that use
            # "snippet" or "content" instead.
            if not excerpts:
                excerpts = raw_result.get(
                    "snippet",
                    raw_result.get(
                        "content",
                        []
                    ),
                )

        else:
            title = str(
                getattr(
                    raw_result,
                    "title",
                    ""
                )
            ).strip()

            url = str(
                getattr(
                    raw_result,
                    "url",
                    ""
                )
            ).strip()

            excerpts = getattr(
                raw_result,
                "excerpts",
                None,
            )

            if not excerpts:
                excerpts = getattr(
                    raw_result,
                    "snippet",
                    getattr(
                        raw_result,
                        "content",
                        [],
                    ),
                )

        if not title or not url:
            return None

        content = ParallelSearchProvider._normalise_excerpts(
            excerpts
        )

        return SearchResult(
            title=title,
            url=url,
            content=content,
            source="parallel",
        )

    @staticmethod
    def _normalise_excerpts(
        excerpts: Any,
    ) -> str:
        """
        Convert Parallel excerpts/content into a single
        application-level content string.
        """

        if excerpts is None:
            return ""

        if isinstance(excerpts, str):
            return excerpts.strip()

        if isinstance(excerpts, list):
            return "\n\n".join(
                str(excerpt).strip()
                for excerpt in excerpts
                if str(excerpt).strip()
            )

        return str(excerpts).strip()
