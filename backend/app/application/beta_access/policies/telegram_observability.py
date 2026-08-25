from __future__ import annotations

import logging
from typing import Any

from backend.app.application.privacy.privacy_identifier_service import (
    PrivacyIdentifierService,
)


logger = logging.getLogger(__name__)


class LoggingTelegramObservability:
    """Non-blocking operational telemetry for the Telegram classroom.

    Raw Telegram IDs and learner content are never written to the log.
    The identity is pseudonymised through the platform privacy service.
    """

    def __init__(
        self,
        *,
        privacy_identifier_service: PrivacyIdentifierService,
    ) -> None:
        if privacy_identifier_service is None:
            raise ValueError(
                "privacy_identifier_service cannot be None."
            )

        self._privacy = privacy_identifier_service

    async def record(
        self,
        *,
        event_type: str,
        telegram_user_id: int,
        outcome: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        try:
            user_hash = self._privacy.pseudonymize_identifier(
                str(telegram_user_id)
            )

            safe_metadata = {
                key: value
                for key, value in (metadata or {}).items()
                if key
                in {
                    "world_id",
                    "character",
                    "level",
                    "error_type",
                }
            }

            logger.info(
                "Telegram classroom event type=%s outcome=%s "
                "user_hash=%s metadata=%s",
                event_type,
                outcome,
                user_hash,
                safe_metadata,
            )
        except Exception:
            # Observability is non-blocking infrastructure.
            logger.exception(
                "Telegram observability recording failed."
            )


__all__ = ["LoggingTelegramObservability"]
