from governance.timeline.governance_timeline_service import (
    GovernanceTimelineService,
)


def test_timeline_records_governance_event():

    service = GovernanceTimelineService()

    event = service.add_event(
        event="PROVIDER_PAUSED",
        component="openai",
        actor="admin",
        reason="External provider incident",
        severity="CRITICAL",
    )

    assert event.event_id == "EVT-001"
    assert event.event == "PROVIDER_PAUSED"
    assert event.evidence_available is True


def test_timeline_is_read_only():

    service = GovernanceTimelineService()

    assert not hasattr(service, "execute")
    assert not hasattr(service, "approve")

