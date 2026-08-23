"""
Provider-independent models for Cybersecurity Intelligence.

These models contain supplied security information only.

They:
- validate normalized cybersecurity observations;
- remain provider-independent;
- contain no external integrations;
- perform no security actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


_ALLOWED_SEVERITIES = {
    "critical",
    "high",
    "medium",
    "low",
    "info",
}


@dataclass(frozen=True, slots=True)
class CybersecuritySignal:
    """
    A normalized cybersecurity observation supplied by
    an application or approved data source.
    """

    signal_id: str
    category: str
    title: str
    severity: str
    confidence: float = 0.0
    source: str = ""
    affected_area: str = ""
    technique: str = ""
    status: str = "open"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.signal_id.strip():
            raise ValueError("signal_id cannot be empty.")

        if not self.category.strip():
            raise ValueError("category cannot be empty.")

        if not self.title.strip():
            raise ValueError("title cannot be empty.")

        severity = self.severity.strip().lower()

        if severity not in _ALLOWED_SEVERITIES:
            raise ValueError(
                f"Unsupported severity: {self.severity!r}."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        object.__setattr__(
            self,
            "severity",
            severity,
        )