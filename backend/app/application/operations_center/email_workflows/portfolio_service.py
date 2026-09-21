from __future__ import annotations

from typing import Any

from app.application.operations_center.email_workflows.registry import (
    EmailWorkflowRegistry,
)


class EmailWorkflowPortfolioService:
    """Build the Operations Center email workflow portfolio.

    The Email Workflow Registry is authoritative for workflow identity,
    definition and lifecycle. Scheduler information is runtime evidence only.
    """

    def __init__(
        self,
        registry: EmailWorkflowRegistry,
        scheduler_runtime: Any,
        provider_manager: Any | None = None,
    ) -> None:
        if registry is None:
            raise ValueError("registry cannot be None.")
        if scheduler_runtime is None:
            raise ValueError("scheduler_runtime cannot be None.")

        self._registry = registry
        self._scheduler_runtime = scheduler_runtime
        self._provider_manager = provider_manager

    def snapshot(self) -> dict[str, Any]:
        provider = self._provider_status()
        scheduler = self._scheduler_status()
        scheduler_jobs = self._scheduler_jobs()

        workflows = [
            self._workflow_payload(workflow, scheduler_jobs, provider)
            for workflow in self._registry.list()
        ]

        return {
            "status": "ready",
            "scheduler": scheduler,
            "provider": provider,
            "workflows": workflows,
            "count": len(workflows),
        }

    def get(self, workflow_id: str) -> dict[str, Any] | None:
        workflow = self._registry.get(workflow_id)
        if workflow is None:
            return None

        provider = self._provider_status()
        scheduler_jobs = self._scheduler_jobs()

        return self._workflow_payload(
            workflow,
            scheduler_jobs,
            provider,
        )

    def _scheduler_jobs(self) -> dict[str, Any]:
        adapter = getattr(
            self._scheduler_runtime,
            "scheduler_adapter",
            None,
        )
        scheduler = getattr(adapter, "scheduler", None)

        if scheduler is None or not hasattr(scheduler, "get_jobs"):
            return {}

        return {
            str(getattr(job, "id", "")): job
            for job in scheduler.get_jobs()
            if getattr(job, "id", None)
        }

    def _scheduler_status(self) -> dict[str, Any]:
        adapter = getattr(
            self._scheduler_runtime,
            "scheduler_adapter",
            None,
        )
        scheduler = getattr(adapter, "scheduler", None)

        return {
            "running": bool(
                getattr(scheduler, "running", False)
            ),
            "adapter_enabled": adapter is not None,
        }

    def _provider_status(self) -> dict[str, Any]:
        if self._provider_manager is None:
            return {
                "provider": None,
                "configured": False,
                "available": False,
                "status": "not_configured",
            }

        return dict(self._provider_manager.status())

    def _workflow_payload(
        self,
        workflow: Any,
        scheduler_jobs: dict[str, Any],
        provider: dict[str, Any],
    ) -> dict[str, Any]:
        job = scheduler_jobs.get(workflow.workflow_id)

        next_run = (
            getattr(job, "next_run_time", None)
            if job is not None
            else None
        )

        scheduler_registered = job is not None

        return {
            "id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "type": workflow.workflow_type.value,
            "category": workflow.owner,
            "trigger": workflow.trigger,
            "schedule": workflow.schedule,
            "template_id": workflow.template_id,
            "version": workflow.version,
            "lifecycle": workflow.lifecycle.value,
            "registered": scheduler_registered,
            "enabled": workflow.lifecycle.value == "ACTIVE",
            "operational_status": (
                "ready"
                if provider.get("available", False)
                else "provider_not_configured"
            ),
            "next_run": (
                next_run.isoformat()
                if next_run is not None
                else None
            ),
        }


__all__ = ["EmailWorkflowPortfolioService"]