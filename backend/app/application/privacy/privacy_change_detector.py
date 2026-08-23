from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PrivacyChangeDetection:
    """Deterministic result of privacy-impacting change detection."""

    privacy_impacting: bool
    reasons: tuple[str, ...]


class PrivacyChangeDetector:
    """Detect material privacy dimensions without making governance decisions.

    This component intentionally does not inspect arbitrary source code or
    automatically invent processing activities. It evaluates an explicit
    change descriptor supplied by the application/CI integration.
    """

    _FLAGS = (
        ("data_categories_changed", "data categories changed"),
        ("purpose_changed", "processing purpose changed"),
        ("recipients_changed", "recipients changed"),
        ("retention_changed", "retention changed"),
        ("processor_changed", "processor/subprocessor changed"),
        ("transfer_changed", "international transfer changed"),
        ("automated_decision_changed", "automated decision/profiling changed"),
    )

    def detect(self, change_descriptor: dict[str, Any]) -> PrivacyChangeDetection:
        if change_descriptor is None:
            raise ValueError("change_descriptor cannot be None.")

        reasons = tuple(
            reason
            for key, reason in self._FLAGS
            if bool(change_descriptor.get(key, False))
        )

        # A new processing activity or data-map entry is itself privacy-impacting.
        if change_descriptor.get("new_processing_activity"):
            reasons += ("new processing activity",)
        if change_descriptor.get("new_data_mapping"):
            reasons += ("new data mapping",)

        return PrivacyChangeDetection(
            privacy_impacting=bool(reasons),
            reasons=reasons,
        )
