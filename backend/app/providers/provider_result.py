"""Canonical provider execution result for the live application provider path."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderUsage:
    """Provider-neutral execution usage metadata.

    Values are optional because not every provider exposes every metric.
    Providers must never invent token counts or request IDs.
    """

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("input_tokens", self.input_tokens),
            ("output_tokens", self.output_tokens),
            ("total_tokens", self.total_tokens),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} cannot be negative.")

        if (
            self.total_tokens is not None
            and self.input_tokens is not None
            and self.output_tokens is not None
            and self.total_tokens < self.input_tokens + self.output_tokens
        ):
            raise ValueError(
                "total_tokens cannot be less than input_tokens + output_tokens."
            )


@dataclass(frozen=True, slots=True)
class ProviderResult:
    """Provider-independent result returned by every live LLM adapter.

    Provider SDK objects must never cross this boundary.

    ``content`` is the canonical generated text. ``output`` is retained as
    a compatibility property for consumers that already use that name.
    """

    success: bool
    provider_id: str
    model: str
    content: str = ""
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    provider_request_id: str | None = None
    latency_ms: float | None = None
    completed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.provider_id.strip():
            raise ValueError("ProviderResult requires provider_id.")
        if not self.model.strip():
            raise ValueError("ProviderResult requires model.")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative.")
        if self.success and not self.content.strip():
            raise ValueError(
                "Successful ProviderResult requires non-empty content."
            )
        if not self.success and not self.error:
            raise ValueError(
                "Failed ProviderResult requires an error."
            )

    @property
    def output(self) -> str:
        """Backward-compatible alias for canonical ``content``."""
        return self.content
