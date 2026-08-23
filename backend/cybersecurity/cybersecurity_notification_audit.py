"""
Cybersecurity Notification Audit.

Stores notification preparation history.

Current implementation:
- in-memory audit.

Future:
- database persistence.
"""

from __future__ import annotations



class CybersecurityNotificationAudit:


    def __init__(
        self,
    ) -> None:

        self._events = []



    def record(
        self,
        event,
    ) -> None:

        self._events.append(
            event
        )



    def get_events(
        self,
    ) -> list:

        return list(
            self._events
        )