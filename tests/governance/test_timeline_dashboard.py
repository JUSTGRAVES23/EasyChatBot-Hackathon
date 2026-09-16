from governance.operations_center.governance_timeline_dashboard_service import (
    GovernanceTimelineDashboardService,
)


def test_dashboard_summary():

    service = GovernanceTimelineDashboardService()

    event = type(
        "Event",
        (),
        {"evidence_available": True},
    )()

    result = service.build_dashboard(
        [event]
    )

    assert result["total_events"] == 1
    assert result["evidence_available"] == 1

