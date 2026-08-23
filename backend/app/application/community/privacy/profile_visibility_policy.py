from __future__ import annotations


class ProfileVisibilityPolicy:
    """Community profiles are private by default."""

    DEFAULT_VISIBILITY = "PRIVATE"

    ALLOWED_PUBLIC_FIELDS = [
        "username",
        "photo",
        "achievements",
        "badges",
    ]
