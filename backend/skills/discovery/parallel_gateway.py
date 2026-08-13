"""
Parallel Discovery Gateway.

Adapts the existing ParallelSearchProvider to the
provider-independent DiscoveryGateway contract.

This adapter belongs at the infrastructure boundary.

Architecture:

ContentProductDiscoverySkill
|
v
DiscoveryGateway
|
v
ParallelDiscoveryGateway
|
v
ParallelSearchProvider
|
v
ParallelClientWrapper
|
v
Parallel API
"""

from __future__ import annotations


from backend.providers.parallel.parallel_provider import (
    ParallelSearchProvider,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)

from backend.skills.discovery.content_product_discovery import (
    DiscoveryCandidate,
    DiscoveryGateway,
)

from backend.skills.discovery.query_generation import (
    DiscoveryQuery,
)


class ParallelDiscoveryGateway:
    """
    DiscoveryGateway implementation backed by Parallel.

    The Discovery Skill remains unaware of Parallel.

    Provider creation remains outside this class and
    is owned by application composition.
    """

    def __init__(
        self,
        provider: ParallelSearchProvider,
    ) -> None:
        """
        Initialise Parallel discovery gateway.

        Args:
            provider:
                Injected Parallel search provider.

        Raises:
            ValueError:
                If provider is missing.
        """

        if provider is None:
            raise ValueError(
                "ParallelSearchProvider cannot be None."
            )

        self.provider = provider


    async def discover(
        self,
        query: DiscoveryQuery,
    ) -> list[DiscoveryCandidate]:
        """
        Execute a discovery query through Parallel.

        The gateway converts provider output into the
        provider-independent DiscoveryCandidate contract.
        """

        context = ExecutionContext(
            user_id="discovery-system",
            request=query.query,
            metadata={
                "content_type": query.content_type,
                "topics": query.topics,
                "languages": query.languages,
                "learning_level": query.learning_level,
                "constraints": query.constraints,
            },
        )

        result = await self.provider.execute(
            context,
        )

        if not result.success:
            raise RuntimeError(
                result.error
                or "Parallel discovery failed."
            )

        return self._normalise_results(
            result.output,
            content_type=query.content_type,
        )


    @staticmethod
    def _normalise_results(
        provider_output,
        *,
        content_type: str,
    ) -> list[DiscoveryCandidate]:
        """
        Convert Parallel provider output into
        provider-independent discovery candidates.
        """

        if not isinstance(
            provider_output,
            dict,
        ):
            return []


        raw_results = provider_output.get(
            "results",
            [],
        )


        if isinstance(
            raw_results,
            dict,
        ):
            raw_results = raw_results.get(
                "results",
                [],
            )


        if not isinstance(
            raw_results,
            list,
        ):
            return []


        candidates: list[DiscoveryCandidate] = []


        for raw_result in raw_results:

            if not isinstance(
                raw_result,
                dict,
            ):
                continue


            title = str(
                raw_result.get(
                    "title",
                    "",
                )
            ).strip()


            url = str(
                raw_result.get(
                    "url",
                    "",
                )
            ).strip()


            if not title or not url:
                continue


            candidates.append(
                DiscoveryCandidate(
                    title=title,
                    url=url,
                    description=(
                        ParallelDiscoveryGateway
                        ._extract_description(
                            raw_result,
                        )
                    ),
                    content_type=content_type,
                    source="parallel",
                    metadata={
                        "raw_result": raw_result,
                    },
                )
            )


        return candidates


    @staticmethod
    def _extract_description(
        raw_result: dict,
    ) -> str:
        """
        Extract provider-neutral description from
        normalized Parallel result.
        """

        excerpts = raw_result.get(
            "excerpts",
        )


        if excerpts is None:
            excerpts = raw_result.get(
                "snippet",
                raw_result.get(
                    "content",
                    "",
                ),
            )


        if isinstance(
            excerpts,
            list,
        ):
            return "\n\n".join(
                str(item).strip()
                for item in excerpts
                if str(item).strip()
            )


        return str(
            excerpts or "",
        ).strip()