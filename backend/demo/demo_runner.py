from .demo_response import DemoResponse


class DemoRunner:
    """
    Demo orchestration boundary.

    Purpose:
    Demonstrate:
    Event -> Email -> Audit -> Timeline -> YETI

    Does not execute production controls.
    """


    async def run(
        self,
        scenario: str,
        event: dict,
    ) -> DemoResponse:

        email = {
            "status": "prepared",
            "subject": f"[DEMO] {event['event']}",
        }

        audit = {
            "event": event["event"],
            "component": event["component"],
            "status": "recorded",
        }

        timeline = {
            "event": event["event"],
            "evidence_available": True,
        }

        yeti = (
            f"🧊 YETI Governance Assistant: "
            f"I detected {event['event']} "
            f"for {event['component']}. "
            f"Evidence is available."
        )

        return DemoResponse(
            scenario=scenario,
            event=event,
            email=email,
            audit=audit,
            timeline=timeline,
            yeti_message=yeti,
        )
