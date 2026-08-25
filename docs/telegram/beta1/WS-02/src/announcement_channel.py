from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnnouncementChannelConfig:
    channel_id: str
    channel_username: str
    application_url: str
    issue_url: str
    publishing_enabled: bool = False


class AnnouncementChannelConfigurationError(ValueError):
    """Raised when announcement-channel configuration is invalid."""


def validate_channel_config(
    config: AnnouncementChannelConfig,
) -> None:
    if not config.channel_id.strip():
        raise AnnouncementChannelConfigurationError("channel_id is required.")

    if not config.application_url.strip():
        raise AnnouncementChannelConfigurationError(
            "application_url is required."
        )

    if not config.issue_url.strip():
        raise AnnouncementChannelConfigurationError("issue_url is required.")

    if not config.channel_username.strip():
        raise AnnouncementChannelConfigurationError(
            "channel_username is required."
        )
