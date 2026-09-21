from __future__ import annotations

from typing import Any

from app.application.operations_center.email_workflows.portfolio_service import (
    EmailWorkflowPortfolioService,
)
from app.application.operations_center.email_workflows.registry import (
    EmailWorkflowRegistry,
)


class EmailWorkflowStatusService:
    """Operations Center facade for the authoritative email workflow portfolio.

    The Email Workflow Registry is authoritative for workflow identity,
    definition and lifecycle.

    Scheduler information is runtime/execution information only.
    """

    def __init__(
        self,
        scheduler_runtime: Any,
        provider_manager: Any = None,
        registry: EmailWorkflowRegistry | None = None,
    ) -> None:
        if scheduler_runtime is None:
            raise ValueError("scheduler_runtime cannot be None.")

        if registry is None:
            raise ValueError("registry is required.")

        self._service = EmailWorkflowPortfolioService(
            registry=registry,
            scheduler_runtime=scheduler_runtime,
            provider_manager=provider_manager,
        )

    def snapshot(self) -> dict[str, Any]:
        """Return the authoritative email workflow portfolio snapshot."""

        return self._service.snapshot()

    def get(self, workflow_id: str) -> dict[str, Any] | None:
        """Return one authoritative email workflow, if it exists."""

        return self._service.get(workflow_id)


__all__ = ["EmailWorkflowStatusService"]