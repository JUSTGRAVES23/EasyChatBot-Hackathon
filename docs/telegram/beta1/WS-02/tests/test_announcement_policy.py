import pytest

from src.announcement_policy import (
    Announcement,
    AnnouncementPolicy,
    AnnouncementPolicyError,
    AnnouncementType,
)


def test_valid_announcement_passes():
    AnnouncementPolicy().validate(
        Announcement(
            announcement_type=AnnouncementType.NEW_FEATURE,
            title="New pronunciation practice",
            body="A new pronunciation activity is now available.",
        )
    )


@pytest.mark.parametrize(
    "title,body",
    [
        ("", "Valid body"),
        ("Valid title", ""),
    ],
)
def test_required_content_is_enforced(title, body):
    with pytest.raises(AnnouncementPolicyError):
        AnnouncementPolicy().validate(
            Announcement(
                announcement_type=AnnouncementType.IMPORTANT,
                title=title,
                body=body,
            )
        )


def test_title_length_is_limited():
    with pytest.raises(AnnouncementPolicyError):
        AnnouncementPolicy().validate(
            Announcement(
                announcement_type=AnnouncementType.IMPORTANT,
                title="x" * 121,
                body="Body",
            )
        )


def test_body_length_is_limited():
    with pytest.raises(AnnouncementPolicyError):
        AnnouncementPolicy().validate(
            Announcement(
                announcement_type=AnnouncementType.IMPORTANT,
                title="Title",
                body="x" * 1801,
            )
        )
