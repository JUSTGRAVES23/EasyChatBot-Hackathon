from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque


class InMemoryTelegramRateLimiter:
    """
    Per-Telegram-identity sliding-window rate limiter.

    Application policy only.

    Does NOT:
        - access Telegram
        - access persistence
        - generate learner-facing messages
    """

    def __init__(
        self,
        *,
        max_messages: int = 100,
        window_seconds: float = 86400.0,
    ) -> None:
        if max_messages <= 0:
            raise ValueError(
                "max_messages must be greater than zero."
            )

        if window_seconds <= 0:
            raise ValueError(
                "window_seconds must be greater than zero."
            )

        self.max_messages = max_messages
        self.window_seconds = float(window_seconds)

        self._events: dict[
            int,
            deque[float],
        ] = defaultdict(deque)

        self._lock = asyncio.Lock()

    async def allow(
        self,
        *,
        telegram_user_id: int,
    ) -> bool:
        now = time.monotonic()

        async with self._lock:
            events = self._events[
                telegram_user_id
            ]

            cutoff = (
                now - self.window_seconds
            )

            self._remove_expired(
                events,
                cutoff,
            )

            if len(events) >= self.max_messages:
                return False

            events.append(now)

            return True

    async def retry_after_seconds(
        self,
        *,
        telegram_user_id: int,
    ) -> float:
        """
        Return the approximate number of seconds until
        the oldest active event leaves the rate-limit window.

        Returns zero when the identity is currently not blocked.
        """

        now = time.monotonic()

        async with self._lock:
            events = self._events.get(
                telegram_user_id
            )

            if not events:
                return 0.0

            cutoff = (
                now - self.window_seconds
            )

            self._remove_expired(
                events,
                cutoff,
            )

            if len(events) < self.max_messages:
                return 0.0

            oldest = events[0]

            return max(
                0.0,
                (
                    oldest
                    + self.window_seconds
                    - now
                ),
            )

    async def reset(
        self,
        *,
        telegram_user_id: int,
    ) -> None:
        async with self._lock:
            self._events.pop(
                telegram_user_id,
                None,
            )

    @staticmethod
    def _remove_expired(
        events: deque[float],
        cutoff: float,
    ) -> None:
        while events and events[0] <= cutoff:
            events.popleft()


__all__ = [
    "InMemoryTelegramRateLimiter",
]