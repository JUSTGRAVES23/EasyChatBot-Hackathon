"""
Cybersecurity Schedule Configuration.

Controlled configuration only.
"""

from __future__ import annotations


class CybersecurityScheduleConfiguration:

    daily_hour = 8
    daily_minute = 0

    weekly_day = "MONDAY"
    weekly_hour = 8
    weekly_minute = 0

    critical_trigger = "IMMEDIATE"


    @classmethod
    def get_configuration(cls):
        return {
            "daily": "08:00",
            "weekly": "MONDAY 08:00",
            "critical": "IMMEDIATE",
        }
