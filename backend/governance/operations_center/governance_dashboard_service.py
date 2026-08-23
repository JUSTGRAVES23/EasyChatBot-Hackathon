
"""
Governance Dashboard Service.

Read-only operations center projection.

Does NOT:
- modify controls;
- pause providers;
- resume delivery;
- execute workflows.
"""

from __future__ import annotations


class GovernanceDashboardService:
    """
    Builds a read model for the Operations Center.
    """

    def __init__(
        self,
        audit_service=None,
        provider_control=None,
        cybersecurity_control=None,
    ) -> None:

        self.audit_service = audit_service
        self.provider_control = provider_control
        self.cybersecurity_control = cybersecurity_control


    def get_status(self) -> dict:
        """
        Return governance dashboard state.
        """

        controls = []

        if self.provider_control:

            controls.append(
                {
                    "component": "provider_management",
                    "status": (
                        "paused"
                        if self.provider_control.is_paused()
                        else "active"
                    ),
                    "details": (
                        self.provider_control.status()
                    ),
                }
            )


        if self.cybersecurity_control:

            controls.append(
                {
                    "component": "cybersecurity_delivery",
                    "status": (
                        "paused"
                        if self.cybersecurity_control.is_paused()
                        else "active"
                    ),
                    "details": (
                        self.cybersecurity_control.status()
                    ),
                }
            )


        events = []

        if self.audit_service:

            events = [
                {
                    "event": item.event,
                    "actor": item.actor,
                    "reason": item.reason,
                    "component": item.component,
                    "timestamp": (
                        item.timestamp.isoformat()
                    ),
                }
                for item in self.audit_service.list_events()
            ]


        return {
            "controls": controls,
            "recent_events": events,
        }
