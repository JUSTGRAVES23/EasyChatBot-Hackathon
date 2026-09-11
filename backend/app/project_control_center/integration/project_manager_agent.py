from __future__ import annotations

from ..domain.models import ProjectControlSnapshot


class ProjectManagerAgentContextBuilder:
    """
    Boundary for the EXISTING Project Manager Agent.

    This class does not execute an agent and does not call an LLM.
    It converts trusted, read-only project facts into an agent context.
    """

    @staticmethod
    def build(snapshot: ProjectControlSnapshot) -> dict[str, object]:
        return {
            "project": {
                "id": snapshot.project_id,
                "name": snapshot.project_name,
                "status": snapshot.project_status.value,
                "progress_percent": snapshot.overall_progress_percent,
                "release_readiness": snapshot.release_readiness,
            },
            "delivery": {
                "current_milestone": snapshot.current_milestone,
                "current_workstream": snapshot.current_workstream,
                "open_blockers": snapshot.open_blockers,
                "open_risks": snapshot.open_risks,
            },
            "workstreams": [
                {
                    "id": w.workstream_id,
                    "name": w.name,
                    "progress_percent": w.completion_percent,
                    "status": w.status.value,
                    "source": w.source,
                }
                for w in snapshot.workstreams
            ],
            "issues": [
                {
                    "id": i.issue_id,
                    "title": i.title,
                    "severity": i.severity.value,
                    "status": i.status.value,
                    "workstream_id": i.workstream_id,
                }
                for i in snapshot.issues
            ],
            "risks": [
                {
                    "id": r.risk_id,
                    "title": r.title,
                    "severity": r.severity.value,
                    "status": r.status,
                    "workstream_id": r.workstream_id,
                }
                for r in snapshot.risks
            ],
            "actions": [
                {
                    "id": a.action_id,
                    "title": a.title,
                    "priority": a.priority.value,
                    "status": a.status.value,
                    "owner": a.owner,
                }
                for a in snapshot.actions
            ],
            "rules": [
                "Use only supplied facts.",
                "Do not invent missing project data.",
                "Separate facts from interpretation.",
                "Do not change project state.",
                "Recommendations are advisory unless separately authorised.",
            ],
        }

    @staticmethod
    def build_summary_instruction(snapshot: ProjectControlSnapshot) -> str:
        context = ProjectManagerAgentContextBuilder.build(snapshot)
        return (
            "Prepare a concise project-management briefing from the supplied "
            f"structured context for project {snapshot.project_name}. "
            "Report current status, progress, blockers, material risks, "
            "recent/active actions and the recommended next management focus. "
            "Explicitly identify unavailable or stale sources. "
            "Do not invent facts or perform actions."
        )
