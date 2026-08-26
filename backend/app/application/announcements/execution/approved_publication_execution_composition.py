"""WS-23.1.4 composition boundary.

Reuses the already-composed WS-22 durable execution service.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.application.announcements.execution.approved_publication_execution import (
    ApprovedPublicationExecutionService,
)
from backend.app.application.announcements.execution.durable_execution_service import (
    DurablePublicationExecutionService,
)


@dataclass(frozen=True, slots=True)
class ApprovedPublicationExecutionComposition:
    service: ApprovedPublicationExecutionService
    durable_execution: DurablePublicationExecutionService


def create_approved_publication_execution_composition(
    *,
    durable_execution: DurablePublicationExecutionService,
) -> ApprovedPublicationExecutionComposition:
    """Compose WS-23.1.4 without creating any new infrastructure."""

    if durable_execution is None:
        raise ValueError("durable_execution cannot be None.")

    service = ApprovedPublicationExecutionService(
        durable_execution=durable_execution,
    )

    return ApprovedPublicationExecutionComposition(
        service=service,
        durable_execution=durable_execution,
    )


__all__ = [
    "ApprovedPublicationExecutionComposition",
    "create_approved_publication_execution_composition",
]
