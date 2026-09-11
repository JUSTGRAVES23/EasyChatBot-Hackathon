from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.project_control_center.application.service import (
    ProjectControlService,
)
from app.project_control_center.domain.models import (
    ProjectDefinition,
    ProjectStatus,
    SourceSnapshot,
    SourceStatus,
    WorkstreamSnapshot,
    WorkstreamStatus,
)
from app.project_control_center.domain.ports import ProjectStatusSource
from app.project_control_center.infrastructure.in_memory import (
    InMemoryProjectRegistry,
    InMemorySnapshotRepository,
)
from app.project_control_center.integration.project_manager_service import (
    ProjectManagerAgentService,
)


@dataclass
class AgentTestSource(ProjectStatusSource):
    @property
    def source_id(self) -> str:
        return "agent-test"

    @property
    def source_name(self) -> str:
        return "Agent Test Source"

    def health(self) -> SourceSnapshot:
        return SourceSnapshot(
            source_id=self.source_id,
            name=self.source_name,
            status=SourceStatus.AVAILABLE,
            updated_at=datetime.now(timezone.utc),
        )

    def fetch_workstreams(
        self,
        project_id: str,
    ) -> list[WorkstreamSnapshot]:
        return [
            WorkstreamSnapshot(
                workstream_id="engineering",
                name="Engineering",
                completion_percent=90,
                status=WorkstreamStatus.HEALTHY,
                source=self.source_id,
            )
        ]

    def fetch_metrics(self, project_id: str):
        return []

    def fetch_issues(self, project_id: str):
        return []

    def fetch_risks(self, project_id: str):
        return []

    def fetch_actions(self, project_id: str):
        return []

    def fetch_milestones(self, project_id: str):
        return []


def make_service() -> ProjectManagerAgentService:
    registry = InMemoryProjectRegistry()

    registry.save(
        ProjectDefinition(
            project_id="easychatbot",
            name="EasyChatBot",
        )
    )

    project_control = ProjectControlService(
        registry=registry,
        sources=(AgentTestSource(),),
        snapshots=InMemorySnapshotRepository(),
    )

    return ProjectManagerAgentService(
        project_control=project_control,
    )


def test_none_project_control_is_rejected():
    with pytest.raises(
        ValueError,
        match="project_control cannot be None",
    ):
        ProjectManagerAgentService(
            project_control=None,  # type: ignore[arg-type]
        )


def test_build_context_returns_governed_project_context():
    service = make_service()

    context = service.build_context(
        "easychatbot",
    )

    assert context["project"]["id"] == "easychatbot"
    assert context["project"]["name"] == "EasyChatBot"
    assert context["project"]["status"] == ProjectStatus.ON_TRACK.value


def test_context_contains_safety_rules():
    service = make_service()

    context = service.build_context(
        "easychatbot",
    )

    rules = context["rules"]

    assert "Use only supplied facts." in rules
    assert "Do not invent missing project data." in rules
    assert "Separate facts from interpretation." in rules
    assert "Do not change project state." in rules
    assert (
        "Recommendations are advisory unless separately authorised."
        in rules
    )


def test_build_context_does_not_persist_by_default():
    service = make_service()

    service.build_context(
        "easychatbot",
    )

    assert (
        service.project_control.snapshots
        .list_for_project("easychatbot")
        == []
    )


def test_build_context_can_explicitly_persist():
    service = make_service()

    service.build_context(
        "easychatbot",
        persist=True,
    )

    assert (
        service.project_control.snapshots
        .list_for_project("easychatbot")
    )


@pytest.mark.asyncio
async def test_build_context_async_returns_governed_context():
    service = make_service()

    context = await service.build_context_async(
        "easychatbot",
    )

    assert context["project"]["id"] == "easychatbot"
    assert context["project"]["name"] == "EasyChatBot"


def test_build_summary_instruction_is_not_provider_execution():
    service = make_service()

    instruction = service.build_summary_instruction(
        "easychatbot",
    )

    assert isinstance(instruction, str)
    assert "EasyChatBot" in instruction
    assert "Do not invent facts or perform actions." in instruction


@pytest.mark.asyncio
async def test_build_summary_instruction_async_is_not_provider_execution():
    service = make_service()

    instruction = (
        await service.build_summary_instruction_async(
            "easychatbot",
        )
    )

    assert isinstance(instruction, str)
    assert "EasyChatBot" in instruction
    assert "Do not invent facts or perform actions." in instruction


def test_unknown_project_is_rejected():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="Unknown project: missing",
    ):
        service.build_context(
            "missing",
        )
