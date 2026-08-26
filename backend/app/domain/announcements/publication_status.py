"""Canonical publication lifecycle status.

WS-22.0.x establishes the lifecycle used by the newer Publication
aggregate while preserving compatibility with the original Announcement
Operations foundation.

Canonical lifecycle:

    DRAFT
        ↓
    PENDING_APPROVAL
        ↓
    APPROVED
        ↓
    PUBLISHING
        ├──→ PUBLISHED
        └──→ FAILED

Compatibility aliases are retained for the existing Announcement
Operations aggregate:

    READY_FOR_REVIEW  -> PENDING_APPROVAL
    PUBLISH_REQUESTED -> PUBLISHING
    ARCHIVED          -> CANCELLED

The aliases intentionally resolve to the canonical enum members. They do
not create another lifecycle or another enum.
"""

from __future__ import annotations

from .template_models import PublicationStatus as _CanonicalPublicationStatus


# ---------------------------------------------------------------------------
# Canonical lifecycle
# ---------------------------------------------------------------------------

PublicationStatus = _CanonicalPublicationStatus


# ---------------------------------------------------------------------------
# Backward-compatible lifecycle aliases
# ---------------------------------------------------------------------------
#
# The original WS-22 Announcement aggregate uses these names.
#
# They MUST resolve to the canonical members rather than becoming separate
# enum values. This preserves enum identity across the application.
# ---------------------------------------------------------------------------

if not hasattr(PublicationStatus, "READY_FOR_REVIEW"):
    PublicationStatus.READY_FOR_REVIEW = (
        PublicationStatus.PENDING_APPROVAL
    )

if not hasattr(PublicationStatus, "PUBLISH_REQUESTED"):
    PublicationStatus.PUBLISH_REQUESTED = (
        PublicationStatus.PUBLISHING
    )

if not hasattr(PublicationStatus, "ARCHIVED"):
    PublicationStatus.ARCHIVED = (
        PublicationStatus.CANCELLED
    )


__all__ = [
    "PublicationStatus",
]