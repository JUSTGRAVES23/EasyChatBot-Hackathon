class GovernanceDemoOrchestrator:
    """
    Demo-only orchestration boundary.

    Demonstrates:
    Event -> Notification -> Audit -> Timeline -> Explanation

    Does not execute production controls.
    """

    def __init__(
        self,
        audit_service=None,
        timeline_service=None,
        email_service=None,
    ):
        self.audit_service = audit_service
        self.timeline_service = timeline_service
        self.email_service = email_service


    async def record_demo_event(
        self,
        *,
        event,
        component,
        reason,
        actor="demo",
        severity="HIGH",
    ):

        result = {
            "event": event,
            "component": component,
            "reason": reason,
            "actor": actor,
            "severity": severity,
        }

        if self.audit_service:
            self.audit_service.record(
                event=event,
                actor=actor,
                reason=reason,
                component=component,
            )

        if self.timeline_service:
            self.timeline_service.add_event(
                event=event,
                component=component,
                actor=actor,
                reason=reason,
                severity=severity,
            )

        return result
