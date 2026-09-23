from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TelegramFailureResponse:
    """Safe, user-facing Telegram representation of an application failure."""

    code: str
    asset_path: str
    message: str
    information_url: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code cannot be empty.")

        if not self.asset_path.strip():
            raise ValueError("asset_path cannot be empty.")

        if not self.message.strip():
            raise ValueError("message cannot be empty.")

        if self.information_url is not None:
            if not self.information_url.strip():
                raise ValueError(
                    "information_url cannot be empty when provided."
                )


PROVIDER_TEMPORARILY_UNAVAILABLE = TelegramFailureResponse(
    code="PROVIDER_TEMPORARILY_UNAVAILABLE",
    asset_path="Provider Temporarily Unavailable.png",
    message=(
        "EasyWorld's AI service is temporarily unavailable.\n\n"
        "We're working to restore it. Please try again shortly."
    ),
)


__all__ = [
    "TelegramFailureResponse",
    "PROVIDER_TEMPORARILY_UNAVAILABLE",
]
