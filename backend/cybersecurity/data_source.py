"""
Cybersecurity data-source contract.

The Cybersecurity Intelligence Agent consumes normalized
CybersecuritySignal objects and remains independent from
the system that supplied them.

Future implementations may use:
- SIEM;
- vulnerability scanners;
- IAM;
- GRC;
- cloud-security tooling;
- approved security providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from cybersecurity.intelligence_models import (
    CybersecuritySignal,
)


class CybersecurityDataSource(ABC):
    """
    Provider-independent source of normalized
    cybersecurity signals.
    """

    source_id: str

    def __init__(
        self,
        source_id: str,
    ) -> None:
        if not source_id.strip():
            raise ValueError(
                "Cybersecurity data source_id cannot be empty."
            )

        self.source_id = source_id

    @abstractmethod
    async def get_signals(
        self,
    ) -> list[CybersecuritySignal]:
        """
        Return normalized cybersecurity observations.
        """
        raise NotImplementedError
