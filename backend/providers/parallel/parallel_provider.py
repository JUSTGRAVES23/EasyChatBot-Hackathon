"""
Parallel Search Provider.

Provides live world information
through the Parallel Search API.
"""

from backend.providers.base_provider import (
    BaseProvider,
)

from backend.providers.provider_result import (
    ProviderResult,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


class ParallelSearchProvider(BaseProvider):
    """
    Provider implementation using Parallel Search.

    The SDK client is created only when required.
    This allows tests to run without API credentials.
    """

    def __init__(
        self,
        client=None,
    ):
        super().__init__(
            provider_id="parallel_search"
        )

        self.client = client


    def _get_client(self):
        """
        Lazy-load the real Parallel client.

        Avoids requiring API keys during unit tests.
        """

        if self.client is None:

            from backend.providers.parallel.parallel_client import (
                ParallelClientWrapper,
            )

            self.client = ParallelClientWrapper()

        return self.client


    async def execute(
        self,
        context: ExecutionContext,
    ) -> ProviderResult:
        """
        Execute a live Parallel search.
        """

        try:

            client = self._get_client()

            result = await client.search(
                query=context.request
            )

            return ProviderResult(
                success=True,
                provider_id=self.provider_id,
                output=result,
            )

        except Exception as exc:

            return ProviderResult(
                success=False,
                provider_id=self.provider_id,
                output=None,
                error=str(exc),
            )