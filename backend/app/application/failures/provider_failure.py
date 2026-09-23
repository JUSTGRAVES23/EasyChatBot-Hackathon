from __future__ import annotations

from dataclasses import dataclass

from app.providers.provider_result import ProviderResult


@dataclass(frozen=True, slots=True)
class ProviderFailure(RuntimeError):
    """Application-level typed representation of a failed LLM request."""

    code: str
    provider_id: str
    provider_request_id: str | None
    message: str
    retryable: bool = True

    def __post_init__(self) -> None:
        if self.code != "PROVIDER_TEMPORARILY_UNAVAILABLE":
            raise ValueError(
                "W19.10-D4 ProviderFailure currently supports only "
                "PROVIDER_TEMPORARILY_UNAVAILABLE."
            )
        if not self.provider_id.strip():
            raise ValueError("provider_id is required.")
        if not self.message.strip():
            raise ValueError("message is required.")

        RuntimeError.__init__(self, self.message)

    @classmethod
    def from_result(cls, result: ProviderResult) -> "ProviderFailure":
        if result.success:
            raise ValueError(
                "ProviderFailure cannot be created from a successful ProviderResult."
            )

        return cls(
            code="PROVIDER_TEMPORARILY_UNAVAILABLE",
            provider_id=result.provider_id,
            provider_request_id=result.provider_request_id,
            message=(
                "The configured AI provider is temporarily unavailable."
            ),
            retryable=True,
        )


__all__ = ["ProviderFailure"]
