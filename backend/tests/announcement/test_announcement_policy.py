import pytest

from app.application.announcement.announcement_policy import (
    AnnouncementPolicy,
    AnnouncementPolicyError,
)
from app.application.announcement.models import Announcement, AnnouncementType


def test_valid_announcement_passes():
    AnnouncementPolicy().validate(
        Announcement(
            announcement_type=AnnouncementType.IMPORTANT,
            title="Important update",
            body="The Beta service remains available.",
        )
    )


@pytest.mark.parametrize(
    ("title", "body"),
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
