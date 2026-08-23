from __future__ import annotations

from .privacy_change import PrivacyChange, PrivacyChangeStatus


class PrivacyChangeRegistry:
    """In-memory application registry for controlled privacy changes.

    Beta 1 intentionally keeps this registry simple. Persistence can be
    introduced behind the same contract once the workflow is proven.
    """

    def __init__(self) -> None:
        self._changes: dict[str, PrivacyChange] = {}

    def register(self, change: PrivacyChange) -> PrivacyChange:
        if change is None:
            raise ValueError("change cannot be None.")
        if change.change_id in self._changes:
            raise ValueError(f"Privacy change already registered: {change.change_id}")
        self._changes[change.change_id] = change
        return change

    def get(self, change_id: str) -> PrivacyChange | None:
        return self._changes.get(change_id)

    def list_all(self) -> list[PrivacyChange]:
        return list(self._changes.values())

    def update(self, change: PrivacyChange) -> PrivacyChange:
        if change is None:
            raise ValueError("change cannot be None.")
        if change.change_id not in self._changes:
            raise KeyError(f"Unknown privacy change: {change.change_id}")
        self._changes[change.change_id] = change
        return change

    def mark_blocked(self, change_id: str) -> PrivacyChange:
        change = self._require(change_id)
        updated = _replace(change, status=PrivacyChangeStatus.BLOCKED)
        self._changes[change_id] = updated
        return updated

    def _require(self, change_id: str) -> PrivacyChange:
        change = self.get(change_id)
        if change is None:
            raise KeyError(f"Unknown privacy change: {change_id}")
        return change


def _replace(change: PrivacyChange, **changes) -> PrivacyChange:
    from dataclasses import replace
    return replace(change, **changes)
