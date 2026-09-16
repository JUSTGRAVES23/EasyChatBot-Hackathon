from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.providers.provider_result import ProviderResult
from src.ai_runtime.providers.usage.models import ProviderUsageEvent
from src.ai_runtime.providers.usage.service import ProviderUsageService


@dataclass(frozen=True, slots=True)
class ProviderUsageContext:
    """Application attribution context for provider usage capture."""

    capability: str
    functionality: str
    agent: str
    quality_score: float = 0.0
    estimated_cost: Decimal = Decimal("0")


class ProviderUsageCapture:
    """
    Translate canonical ProviderResult objects into ProviderUsageEvent objects.

    This class owns application-layer usage capture only.

    It does not:

    - call providers;
    - calculate provider billing;
    - access databases directly;
    - execute agents;
    - own persistence.

    Persistence remains behind ProviderUsageService / repository.
    """

    def __init__(
        self,
        service: ProviderUsageService,
    ) -> None:
        self._service = service

    def capture(
        self,
        *,
        result: ProviderResult,
        context: ProviderUsageContext,
    ) -> ProviderUsageEvent:
        """
        Capture provider execution usage as a canonical usage event.
        """

        if result is None:
            raise ValueError("ProviderResult cannot be None.")

        if context is None:
            raise ValueError("ProviderUsageContext cannot be None.")

        usage = result.usage

        if usage is None:
            # Established compatibility contract for provider results
            # without a usage payload.
            input_tokens = 0
            output_tokens = 0
            total_tokens = None

        elif (
            not result.success
            and usage.input_tokens is None
            and usage.output_tokens is None
            and usage.total_tokens is None
        ):
            # Failed provider executions historically represented the absence
            # of usable usage information as zero input/output tokens.
            #
            # Preserve that contract while allowing successful executions to
            # distinguish unknown usage (None) from real zero usage (0).
            input_tokens = 0
            output_tokens = 0
            total_tokens = None

        else:
            # Provider explicitly supplied a usage object.
            #
            # Preserve values exactly:
            # - None = unknown
            # - 0 = provider-reported zero
            # - positive integer = provider-reported usage
            input_tokens = usage.input_tokens
            output_tokens = usage.output_tokens
            total_tokens = usage.total_tokens

        # Preserve unknown latency as unknown rather than converting it to
        # zero. Zero latency and unknown latency are different semantics.
        latency_ms = (
            int(round(result.latency_ms))
            if result.latency_ms is not None
            else None
        )

        event = ProviderUsageEvent(
            provider=result.provider_id,
            model=result.model,
            capability=context.capability,
            functionality=context.functionality,
            agent=context.agent,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            estimated_cost=context.estimated_cost,
            quality_score=context.quality_score,
            success=result.success,
            total_tokens=total_tokens,
            provider_request_id=result.provider_request_id,
        )

        self._service.record(event)

        return event
