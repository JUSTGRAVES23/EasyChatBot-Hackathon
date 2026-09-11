from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.project_control_center.application.service import (
    ProjectControlService,
)
from app.project_control_center.domain.models import (
    ProjectDefinition,
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
from app.project_control_center.integration.project_manager_agent import (
    ProjectManagerAgentContextBuilder,
)
from app.project_control_center.integration.project_manager_service import (
    ProjectManagerAgentService,
)


@dataclass
class SafetyTestSource(ProjectStatusSource):
    @property
    def source_id(self) -> str:
        return "safety-test"

    @property
    def source_name(self) -> str:
        return "Safety Test Source"

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
                workstream_id="pcd",
                name="Project Control Center",
                completion_percent=80,
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
        sources=(SafetyTestSource(),),
        snapshots=InMemorySnapshotRepository(),
    )

    return ProjectManagerAgentService(
        project_control=project_control,
    )


def test_context_is_limited_to_governed_sections():
    service = make_service()

    context = service.build_context("easychatbot")

    assert set(context) == {
        "project",
        "delivery",
        "workstreams",
        "issues",
        "risks",
        "actions",
        "rules",
    }


def test_context_contains_no_provider_or_execution_controls():
    service = make_service()

    context = service.build_context("easychatbot")
    flattened = repr(context).lower()

    assert "api_key" not in flattened
    assert "secret" not in flattened
    assert "token" not in flattened
    assert "provider" not in flattened
    assert "llm" not in flattened
    assert "execute" not in flattened


def test_context_is_read_only_plain_data():
    service = make_service()

    context = service.build_context("easychatbot")

    assert isinstance(context, dict)
    assert isinstance(context["project"], dict)
    assert isinstance(context["delivery"], dict)
    assert isinstance(context["workstreams"], list)
    assert isinstance(context["issues"], list)
    assert isinstance(context["risks"], list)
    assert isinstance(context["actions"], list)


def test_context_does_not_expose_project_control_service():
    service = make_service()

    context = service.build_context("easychatbot")

    assert service.project_control not in context.values()


def test_agent_context_does_not_mutate_project_state():
    service = make_service()

    before = service.project_control.get_snapshot(
        "easychatbot",
        persist=False,
    )

    context = service.build_context("easychatbot")

    context["project"]["status"] = "tampered"
    context["delivery"]["open_blockers"] = 999
    context["rules"].append("unauthorised action")

    after = service.project_control.get_snapshot(
        "easychatbot",
        persist=False,
    )

    assert after.project_status == before.project_status
    assert after.open_blockers == before.open_blockers
    assert "unauthorised action" not in (
        ProjectManagerAgentContextBuilder.build(before)["rules"]
    )


def test_context_rules_forbid_state_change():
    service = make_service()

    context = service.build_context("easychatbot")
    rules = context["rules"]

    assert "Do not change project state." in rules
    assert (
        "Recommendations are advisory unless separately authorised."
        in rules
    )


def test_summary_instruction_explicitly_forbids_actions():
    service = make_service()

    instruction = service.build_summary_instruction(
        "easychatbot",
    )

    assert "Do not invent facts or perform actions." in instruction
    assert "recommended next management focus" in instruction


def test_unknown_project_cannot_reach_agent_context():
    service = make_service()

    with pytest.raises(
        ValueError,
        match="Unknown project: missing",
    ):
        service.build_context("missing")


@pytest.mark.asyncio
async def test_async_context_preserves_same_governed_boundary():
    service = make_service()

    sync_context = service.build_context("easychatbot")
    async_context = await service.build_context_async("easychatbot")

    assert async_context == sync_context


@pytest.mark.asyncio
async def test_async_summary_instruction_remains_advisory():
    service = make_service()

    instruction = (
        await service.build_summary_instruction_async(
            "easychatbot",
        )
    )

    assert "Do not invent facts or perform actions." in instruction
    assert "recommended next management focus" in instruction


def test_context_does_not_persist_without_explicit_request():
    service = make_service()

    service.build_context("easychatbot")

    assert (
        service.project_control.snapshots
        .list_for_project("easychatbot")
        == []
    )


def test_explicit_persistence_is_the_only_persistence_path():
    service = make_service()

    service.build_context(
        "easychatbot",
        persist=True,
    )

    assert (
        service.project_control.snapshots
        .list_for_project("easychatbot")
    )


def test_context_builder_has_no_execution_method():
    public_methods = {
        name
        for name in dir(ProjectManagerAgentContextBuilder)
        if not name.startswith("_")
    }

    assert public_methods == {
        "build",
        "build_summary_instruction",
    }


def test_service_has_no_direct_provider_dependency():
    service = make_service()

    assert not hasattr(service, "provider")
    assert not hasattr(service, "llm")
    assert not hasattr(service, "execute")
    assert not hasattr(service, "agent_runtime")
