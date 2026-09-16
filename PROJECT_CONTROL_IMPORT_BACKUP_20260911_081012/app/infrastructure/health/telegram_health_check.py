from __future__ import annotations

import os
from typing import Any

from app.application.health.health_result import (
    HealthCheckResult,
    HealthStatus,
)


class TelegramHealthCheck:
    """Read-only Telegram Bot API readiness probe.

    Uses Telegram getMe to verify that the configured bot token
    is valid and the Telegram API is reachable.

    No classroom or announcement-group message is sent.
    """

    name = "telegram"

    def __init__(
        self,
        *,
        bot_factory: Any | None = None,
    ) -> None:
        self._bot_factory = bot_factory

    async def check(self) -> HealthCheckResult:
        token = os.getenv(
            "TELEGRAM_BOT_TOKEN"
        )

        if not token:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.NOT_CONFIGURED,
                details={
                    "configured": False,
                },
            )

        try:
            if self._bot_factory is None:
                from telegram import Bot

                bot = Bot(
                    token=token,
                )
            else:
                bot = self._bot_factory(
                    token,
                )

            try:
                user = await bot.get_me()

            finally:
                shutdown = getattr(
                    bot,
                    "shutdown",
                    None,
                )

                if shutdown is not None:
                    result = shutdown()

                    if hasattr(
                        result,
                        "__await__",
                    ):
                        await result

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                details={
                    "configured": True,
                    "bot_reachable": True,
                    "bot_id_present": bool(
                        getattr(
                            user,
                            "id",
                            None,
                        )
                    ),
                },
            )

        except Exception:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                details={
                    "configured": True,
                    "reason": "telegram_api_unavailable",
                },
            )


__all__ = [
    "TelegramHealthCheck",
]







