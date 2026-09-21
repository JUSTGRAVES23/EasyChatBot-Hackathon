from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class EmailNotificationSender(Protocol):
    async def send(
        self,
        subject: str,
        content: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        ...


class TelegramNotificationSender(Protocol):
    async def send(
        self,
        *,
        chat_id: str,
        text: str,
        portal_url: str,
    ) -> Mapping[str, Any]:
        ...
