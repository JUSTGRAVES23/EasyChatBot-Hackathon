from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.application.academy.academy_notification_delivery import (
    AcademyDeliveryRepository,
    AcademyUserQuery,
)
from app.application.academy_notification_service import (
    OneWeekNotificationOrchestrator,
)


class AcademyOneWeekWorkflow:
    """Execute the Academy 1-week workflow without owning scheduler state."""

    NOTIFICATION_TYPE = "1_WEEK_MILESTONE"

    def __init__(
        self,
        *,
        users: AcademyUserQuery,
        deliveries: AcademyDeliveryRepository,
        notifications: OneWeekNotificationOrchestrator,
        clock=None,
    ) -> None:
        self._users = users
        self._deliveries = deliveries
        self._notifications = notifications
        self._clock = clock or (
            lambda: datetime.now(timezone.utc)
        )

    async def run(self) -> dict[str, int]:
        now = self._clock()

        if now.tzinfo is None:
            raise ValueError(
                "Workflow clock must return a timezone-aware datetime."
            )

        window_start = now - timedelta(days=8)
        window_end = now - timedelta(days=7)

        candidates = await self._users.list_one_week_candidates(
            window_start=window_start,
            window_end=window_end,
        )

        attempted = 0
        succeeded = 0
        skipped = 0
        failed = 0

        for user in candidates:
            # The query is deliberately bounded by the same eligibility
            # window, while the domain rule remains the final guard.
            if not self._notifications.is_one_week_eligible(
                registered_at=user.created_at,
                now=now,
            ):
                skipped += 1
                continue

            claim = await self._deliveries.claim(
                user_id=user.user_id,
                notification_type=self.NOTIFICATION_TYPE,
                now=now,
            )

            if claim is None:
                skipped += 1
                continue

            attempted += 1

            try:
                result = await self._notifications.send_one_week(
                    email=user.email,
                    username=user.username,
                    telegram_chat_id=None,
                )

                email_result = result.get("email") or {}
                provider_message_id = email_result.get(
                    "message_id"
                )

                await self._deliveries.mark_succeeded(
                    user_id=user.user_id,
                    notification_type=self.NOTIFICATION_TYPE,
                    provider_message_id=(
                        str(provider_message_id)
                        if provider_message_id is not None
                        else None
                    ),
                    now=now,
                )

                succeeded += 1

            except Exception as exc:
                await self._deliveries.mark_failed(
                    user_id=user.user_id,
                    notification_type=self.NOTIFICATION_TYPE,
                    error=str(exc)[:2000],
                    now=now,
                )

                failed += 1

        return {
            "candidates": len(candidates),
            "attempted": attempted,
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped,
        }


__all__ = [
    "AcademyOneWeekWorkflow",
]
