from src.announcement_channel import (
    AnnouncementChannelConfig,
    AnnouncementChannelConfigurationError,
    validate_channel_config,
)


def valid_config() -> AnnouncementChannelConfig:
    return AnnouncementChannelConfig(
        channel_id="-100123",
        channel_username="EasyChatBotAcademyBot",
        application_url="https://example.com",
        issue_url="https://example.com/beta/issues",
    )


def test_valid_configuration_passes():
    validate_channel_config(valid_config())


def test_required_configuration_is_enforced():
    for field in (
        "channel_id",
        "channel_username",
        "application_url",
        "issue_url",
    ):
        values = valid_config().__dict__
        values[field] = ""

        try:
            validate_channel_config(
                AnnouncementChannelConfig(**values)
            )
        except AnnouncementChannelConfigurationError:
            continue

        raise AssertionError(f"{field} was not validated")
