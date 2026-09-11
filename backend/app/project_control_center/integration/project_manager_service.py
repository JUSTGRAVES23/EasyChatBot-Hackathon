"""
Project Manager Agent integration service.

This module provides the governed application boundary between the
Project Control Center and the Project Manager Agent.

Responsibilities:

- obtain a ProjectControlSnapshot;
- convert it through ProjectManagerAgentContextBuilder;
- return structured agent context;
- build the management briefing instruction.

This service does NOT:

- execute an LLM;
- select an LLM provider;
- query Health directly;
- query Operations directly;
- query Privacy Governance directly;
- access Git directly;
- access databases directly;
- modify project state;
- execute production actions.

The Project Control Center remains the single composition boundary.
The Project Manager Agent receives only the resulting read-only snapshot
context.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..application.service import ProjectControlService
from .project_manager_agent import (
    ProjectManagerAgentContextBuilder,
)


@dataclass(frozen=True, slots=True)
class ProjectManagerAgentService:
    """
    Governed integration boundary for the Project Manager Agent.

    The service deliberately depends only on ProjectControlService.
    It therefore cannot directly reach the authoritative Health,
    Operations, Privacy Governance, provider, or persistence systems.
    """

    project_control: ProjectControlService

    def __post_init__(self) -> None:
        if self.project_control is None:
            raise ValueError(
                "project_control cannot be None."
            )

    def build_context(
        self,
        project_id: str,
        *,
        persist: bool = False,
    ) -> dict[str, object]:
        """
        Build read-only Project Manager Agent context.

        The context is derived from the ProjectControlSnapshot and
        contains only data exposed by the existing context builder.
        """

        snapshot = self.project_control.get_snapshot(
            project_id,
            persist=persist,
        )

        return ProjectManagerAgentContextBuilder.build(
            snapshot
        )

    async def build_context_async(
        self,
        project_id: str,
        *,
        persist: bool = False,
    ) -> dict[str, object]:
        """
        Build read-only Project Manager Agent context asynchronously.

        This uses the asynchronous Project Control composition path
        required by production-backed PCD adapters.
        """

        snapshot = await self.project_control.get_snapshot_async(
            project_id,
            persist=persist,
        )

        return ProjectManagerAgentContextBuilder.build(
            snapshot
        )

    def build_summary_instruction(
        self,
        project_id: str,
        *,
        persist: bool = False,
    ) -> str:
        """
        Build the management briefing instruction.

        No model/provider is invoked here.
        """

        snapshot = self.project_control.get_snapshot(
            project_id,
            persist=persist,
        )

        return (
            ProjectManagerAgentContextBuilder
            .build_summary_instruction(snapshot)
        )

    async def build_summary_instruction_async(
        self,
        project_id: str,
        *,
        persist: bool = False,
    ) -> str:
        """
        Build the management briefing instruction asynchronously.

        No model/provider is invoked here.
        """

        snapshot = await self.project_control.get_snapshot_async(
            project_id,
            persist=persist,
        )

        return (
            ProjectManagerAgentContextBuilder
            .build_summary_instruction(snapshot)
        )


__all__ = [
    "ProjectManagerAgentService",
]