"""
Cybersecurity Scheduler Configuration.

Central configuration boundary.

Future:
- environment variables;
- YAML configuration;
- enterprise configuration service.
"""

from __future__ import annotations


SCHEDULER_TIMEZONE = (
    "Europe/Luxembourg"
)


DAILY_REPORT_HOUR = 8


DAILY_REPORT_MINUTE = 0



WEEKLY_REPORT_DAY = (
    "mon"
)


WEEKLY_REPORT_HOUR = 8


WEEKLY_REPORT_MINUTE = 0