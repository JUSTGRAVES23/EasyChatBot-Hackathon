"""
Cybersecurity Notification Event.

Represents a controlled notification event.

Does NOT:
- send emails;
- execute actions;
- modify systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass(frozen=True)
class CybersecurityNotificationEvent:
    """
    Immutable notification event record.
    """


    event_type: str

    priority: str

    recipient: str

    status: str = "prepared"

    created_at: str = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )