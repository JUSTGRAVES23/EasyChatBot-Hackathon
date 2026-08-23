from __future__ import annotations

from .privacy_governance_dashboard_service import (
    PrivacyGovernanceDashboardService,
)


class PrivacyGovernanceDashboardAPI:
    """Application-facing read adapter for the privacy governance dashboard."""

    def __init__(
        self,
        *,
        dashboard_service: PrivacyGovernanceDashboardService,
    ) -> None:
        if dashboard_service is None:
            raise ValueError("dashboard_service cannot be None.")
        self._dashboard = dashboard_service

    def get_summary(self) -> dict[str, int]:
        return self._dashboard.summary()

    def get_status_chart(self) -> tuple[dict[str, object], ...]:
        return self._dashboard.status_chart()

    def get_cases(self) -> tuple[dict[str, object], ...]:
        return self._dashboard.case_list()

    def get_case_detail(self, case_id: str) -> dict[str, object]:
        return self._dashboard.case_detail(case_id)


__all__ = ["PrivacyGovernanceDashboardAPI"]
