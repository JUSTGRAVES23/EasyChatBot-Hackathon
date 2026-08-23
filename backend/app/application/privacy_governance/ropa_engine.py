from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProcessingActivity:
    name: str
    purpose: str
    legal_basis: str
    data_categories: list[str]
    retention_policy: str
    processor_dependencies: list[str]


class ROPAEngine:
    """Registry foundation for automated Records of Processing Activities."""

    def __init__(self):
        self._activities: list[ProcessingActivity] = []

    def register(self, activity: ProcessingActivity) -> None:
        self._activities.append(activity)

    def list_activities(self) -> list[ProcessingActivity]:
        return list(self._activities)
