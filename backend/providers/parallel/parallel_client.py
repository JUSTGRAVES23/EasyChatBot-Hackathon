"""
Parallel Search API Client Wrapper.

This module isolates the official Parallel SDK.

The rest of EasyChatBot does not directly depend on
the Parallel SDK implementation.

Architecture:

Research Agent
        |
        v
Parallel Provider
        |
        v
Parallel Client Wrapper
        |
        v
Parallel API
"""

import asyncio
import os
from typing import Any

from dotenv import load_dotenv


load_dotenv()


class ParallelClientWrapper:
    """
    Wrapper around the official Parallel Search SDK.

    Responsibilities:
    - authenticate with Parallel
    - execute searches
    - normalize SDK responses

    Does not:
    - create learning content
    - manage agents
    - decide workflows
    """

    def __init__(
        self,
        api_key: str | None = None,
    ):
        """
        Initialise the Parallel SDK client.
        """

        self.api_key = (
            api_key
            or os.getenv("PARALLEL_API_KEY")
        )

        if not self.api_key:
            raise ValueError(
                "PARALLEL_API_KEY environment variable is required"
            )

        self._client = self._create_client()


    def _create_client(self):
        """
        Create the official Parallel SDK client.

        SDK:
            parallel-web 1.1.0
        """

        from parallel import Parallel

        return Parallel(
            api_key=self.api_key
        )


    @staticmethod
    def _normalize_response(
        response: Any,
    ) -> Any:
        """
        Convert the Parallel SDK response into
        application-safe data.

        Pydantic SDK models are converted to dictionaries.
        Other JSON-compatible values are returned unchanged.
        """

        if hasattr(response, "model_dump"):
            return response.model_dump()

        if hasattr(response, "dict"):
            return response.dict()

        return response


    async def search(
        self,
        query: str,
    ) -> dict[str, Any]:
        """
        Execute a Parallel web search.

        Args:
            query:
                Natural-language research objective.

        Returns:
            Normalized application-level search result.
        """

        search_query = self._build_search_query(
            query
        )

        response = await asyncio.to_thread(
            self._client.search,
            search_queries=[
                search_query
            ],
            mode="advanced",
            objective=query,
        )

        return {
            "query": query,
            "search_queries": [
                search_query
            ],
            "results": self._normalize_response(
                response
            ),
        }


    @staticmethod
    def _build_search_query(
        query: str,
    ) -> str:
        """
        Build a concise search query from the
        user's research request.

        The full request remains the Parallel
        objective while the search query is kept
        concise.
        """

        words = query.strip().split()

        if len(words) <= 6:
            return query.strip()

        return " ".join(words[:6])