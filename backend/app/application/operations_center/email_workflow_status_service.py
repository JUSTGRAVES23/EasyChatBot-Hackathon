from __future__ import annotations

from typing import Any


class EmailWorkflowStatusService:
    """Read-only operational snapshot for scheduled email workflows."""

    _WORKFLOW_METADATA: dict[str, dict[str, Any]] = {
        "cybersecurity_daily_report": {
            "name": "Cybersecurity Daily Report",
            "category": "Cybersecurity",
            "schedule": "Daily at 08:00",
        },
        "cybersecurity_weekly_report": {
            "name": "Cybersecurity Weekly Report",
            "category": "Cybersecurity",
            "schedule": "Monday at 08:00",
        },
        "privacy_governance_reminder": {
            "name": "Privacy Governance Reminder",
            "category": "Privacy",
            "schedule": "Every 60 minutes",
        },
        "academy_one_week_milestone": {
            "name": "Academy One Week Milestone",
            "category": "Academy",
            "schedule": "Daily at 08:15",
        },
    }

    def __init__(self, scheduler_runtime, provider_manager=None) -> None:
        if scheduler_runtime is None:
            raise ValueError("scheduler_runtime cannot be None.")
        self.scheduler_runtime = scheduler_runtime
        self.provider_manager = provider_manager

    def snapshot(self) -> dict[str, Any]:
        provider = self._provider_status()
        workflows = [
            self._workflow_payload(job, provider)
            for job in self._production_jobs()
        ]
        return {
            "status": "ready",
            "scheduler": self._scheduler_status(),
            "provider": provider,
            "workflows": workflows,
            "count": len(workflows),
        }

    def _production_jobs(self) -> list[Any]:
        adapter = getattr(self.scheduler_runtime, "scheduler_adapter", None)
        scheduler = getattr(adapter, "scheduler", None)
        if scheduler is not None and hasattr(scheduler, "get_jobs"):
            return list(scheduler.get_jobs())
        return []

    def _scheduler_status(self) -> dict[str, Any]:
        adapter = getattr(self.scheduler_runtime, "scheduler_adapter", None)
        scheduler = getattr(adapter, "scheduler", None)
        return {
            "running": bool(getattr(scheduler, "running", False)),
            "adapter_enabled": adapter is not None,
        }

    def _provider_status(self) -> dict[str, Any]:
        if self.provider_manager is None:
            return {
                "provider": None,
                "configured": False,
                "available": False,
                "status": "not_configured",
            }
        return dict(self.provider_manager.status())

    def _workflow_payload(self, job: Any, provider: dict[str, Any]) -> dict[str, Any]:
        job_id = str(getattr(job, "id", "unknown"))
        metadata = self._WORKFLOW_METADATA.get(
            job_id,
            {
                "name": job_id,
                "category": "Other",
                "schedule": "Configured scheduler job",
            },
        )
        next_run = getattr(job, "next_run_time", None)
        return {
            "id": job_id,
            "name": metadata["name"],
            "category": metadata["category"],
            "schedule": metadata["schedule"],
            "registered": True,
            "enabled": True,
            "operational_status": (
                "ready"
                if provider.get("available", False)
                else "provider_not_configured"
            ),
            "next_run": next_run.isoformat() if next_run is not None else None,
        }
