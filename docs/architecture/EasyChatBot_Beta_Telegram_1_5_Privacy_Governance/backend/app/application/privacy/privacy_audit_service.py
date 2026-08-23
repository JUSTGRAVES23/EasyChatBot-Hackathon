from __future__ import annotations

from datetime import datetime, timezone


class PrivacyAuditService:
    def create_event(
        self,
        *,
        action: str,
        pseudonymous_id: str,
        source: str,
    ) -> dict:
        return {
            "action": action,
            "pseudonymous_id": pseudonymous_id,
            "source": source,
            "timestamp": datetime.now(timezone.utc),
        }
