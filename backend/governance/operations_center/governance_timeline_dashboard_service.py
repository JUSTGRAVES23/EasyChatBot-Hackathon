class GovernanceTimelineDashboardService:
    """
    Read-only Operations Center aggregation boundary.
    """

    def build_dashboard(self, events):

        return {
            "timeline": events,
            "total_events": len(events),
            "evidence_available": sum(
                1
                for event in events
                if event.evidence_available
            ),
        }
