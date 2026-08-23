"""
Cybersecurity Job Registry.

Registers future scheduled workflows.
"""

from __future__ import annotations


class CybersecurityJobRegistry:

    def __init__(self):
        self.jobs = []


    def register(
        self,
        name: str,
        schedule: str,
    ):
        self.jobs.append(
            {
                "name": name,
                "schedule": schedule,
            }
        )


    def list_jobs(self):
        return list(self.jobs)
