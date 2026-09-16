from __future__ import annotations

from datetime import datetime, timezone


class SystemTrustedClock:
    """Production trusted application clock.

    All security-sensitive freshness and expiry decisions use UTC time
    obtained from the application/server runtime rather than caller-
    supplied timestamps.
    """

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


__all__ = ["SystemTrustedClock"]