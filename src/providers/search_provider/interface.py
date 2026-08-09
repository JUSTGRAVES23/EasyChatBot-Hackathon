"""
Search Provider Interface

Defines the provider-independent contract for external search capabilities.

Architecture:
Agent -> Provider Interface -> Provider Adapter

The agent must never depend directly on a vendor SDK.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class SearchResult:
    """
    Normalised search result returned by any provider.
    """

    title: str
    url: str
    content: str
    source: str


class SearchProvider(ABC):
    """
    Abstract search provider contract.

    Implementations:
    - ParallelSearchProvider
    - Future providers
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> List[SearchResult]:
        """
        Execute a search query.

        Args:
            query:
                Search query.

            max_results:
                Maximum number of results.

        Returns:
            Normalised search results.
        """
        raise NotImplementedError