"""
Cybersecurity Notification Policy.

Configuration-driven notification rules.

Does NOT:
- send emails;
- analyse security;
- execute actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CybersecurityNotificationPolicy:
    """
    Configuration-driven cybersecurity notification policy.
    """

    daily_report_enabled: bool = True

    weekly_report_enabled: bool = True

    critical_alerts_enabled: bool = True

    critical_severity: str = "critical"

    high_priority_alert_enabled: bool = True

    def should_send_daily_report(self) -> bool:
        """
        Return whether daily cybersecurity reports are enabled.
        """

        return self.daily_report_enabled

    def should_send_weekly_report(self) -> bool:
        """
        Return whether weekly cybersecurity reports are enabled.
        """

        return self.weekly_report_enabled

    def should_send_critical_alert(
        self,
        signal_or_report: str | dict[str, Any],
    ) -> bool:
        """
        Determine whether a critical alert should be sent.

        Supports both:

        1. A severity string:

           "critical"

        2. A cybersecurity report:

           {
               "critical_count": 1
           }

        This preserves compatibility with both existing
        application callers and the current test contract.
        """

        if not self.critical_alerts_enabled:
            return False

        if isinstance(signal_or_report, dict):

            critical_count = signal_or_report.get(
                "critical_count",
                0,
            )

            try:
                return int(critical_count) > 0
            except (TypeError, ValueError):
                return False

        if isinstance(signal_or_report, str):

            return (
                signal_or_report.strip().lower()
                == self.critical_severity.lower()
            )

        return False