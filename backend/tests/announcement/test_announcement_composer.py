from app.application.announcement.announcement_composer import AnnouncementComposer
from app.application.announcement.models import AnnouncementType


def test_composer_creates_branded_message():
    result = AnnouncementComposer().compose(
        announcement_type=AnnouncementType.NEW_FEATURE,
        title="New pronunciation practice",
        body="Try the new activity in your classroom.",
    )

    assert "🚀 NEW FEATURE" in result.rendered_text
    assert "New pronunciation practice" in result.rendered_text
    assert "EasyWorld" in result.rendered_text
    assert "Growing with You" in result.rendered_text
