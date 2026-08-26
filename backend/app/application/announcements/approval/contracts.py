from __future__ import annotations

from collections.abc import Awaitable, Callable


AdminAuthorizer = Callable[[], Awaitable[bool]]


__all__ = [
    "AdminAuthorizer",
]