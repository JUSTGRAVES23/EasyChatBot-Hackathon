from __future__ import annotations

from dataclasses import dataclass

from .processing_activity import ProcessingActivity


class ProcessingRegistry:
    """Registry of processing activities exposed by the application.

    The registry is intentionally deterministic and Beta 1 scoped.
    It is a governance input, not a legal approval engine.
    """

    def __init__(self, activities: list[ProcessingActivity] | None = None) -> None:
        self._activities: dict[str, ProcessingActivity] = {}
        for activity in activities or []:
            self.register(activity)

    def register(self, activity: ProcessingActivity) -> None:
        if not activity.processing_id.strip():
            raise ValueError("processing_id is required.")
        if activity.processing_id in self._activities:
            raise ValueError(
                f"Processing activity already registered: {activity.processing_id}"
            )
        self._activities[activity.processing_id] = activity

    def get(self, processing_id: str) -> ProcessingActivity:
        try:
            return self._activities[processing_id]
        except KeyError as exc:
            raise KeyError(
                f"Processing activity not registered: {processing_id}"
            ) from exc

    def all(self) -> tuple[ProcessingActivity, ...]:
        return tuple(self._activities.values())

    def ids(self) -> set[str]:
        return set(self._activities)
