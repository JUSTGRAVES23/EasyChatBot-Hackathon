"""
Cybersecurity Delivery Control.

Manual governance kill switch for cybersecurity delivery.
"""

from __future__ import annotations

from datetime import UTC, datetime

from governance.governance_audit_service import (
    GovernanceAuditService,
)


class CybersecurityDeliveryControl:
    """
    Human-controlled cybersecurity delivery switch.
    """

    def __init__(
        self,
        audit_service: GovernanceAuditService | None = None,
    ) -> None:

        self._paused = False
        self._reason: str | None = None
        self._changed_at: datetime | None = None

        self.audit_service = (
            audit_service
            or GovernanceAuditService()
        )


    def pause(
        self,
        reason: str,
        actor: str = "admin",
    ) -> None:

        if not reason.strip():
            raise ValueError(
                "A pause reason is required."
            )

        self._paused = True
        self._reason = reason.strip()
        self._changed_at = datetime.now(UTC)


        self.audit_service.record(
            event="CYBERSECURITY_DELIVERY_PAUSED",
            actor=actor,
            reason=self._reason,
            component="cybersecurity_delivery",
        )


    def resume(
        self,
        actor: str = "admin",
    ) -> None:

        self._paused = False
        self._reason = None
        self._changed_at = datetime.now(UTC)


        self.audit_service.record(
            event="CYBERSECURITY_DELIVERY_RESUMED",
            actor=actor,
            reason="Manual resume",
            component="cybersecurity_delivery",
        )


    def is_paused(
        self,
    ) -> bool:

        return self._paused


    def allow_execution(
        self,
    ) -> bool:

        return not self._paused


    def status(
        self,
    ) -> dict:

        return {
            "paused": self._paused,
            "reason": self._reason,
            "changed_at": self._changed_at,
        }
