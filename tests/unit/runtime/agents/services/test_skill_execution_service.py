from __future__ import annotations

from types import SimpleNamespace

import pytest

from runtime.agents.services.skill_execution_service import (
    SkillExecutionService,
)


class FakeManifest:
    id = "architecture_review"
    name = "Architecture Review"
    description = "Architecture review."
    version = "1.0.0"
    status = "active"
    owner = "Engineering Board"
    compatible_agents = ["platform_intelligence_agent"]

    def validate(self) -> None:
        return None


class FakeRegistry:
    def __init__(self, manifest=None):
        self.manifest = manifest or FakeManifest()

    def get(self, skill_id: str):
        if skill_id != self.manifest.id:
            raise KeyError(skill_id)
        return self.manifest


class FakeExecutionService:
    def __init__(self):
        self.called = False

    async def execute(self, *, request, context):
        self.called = True
        return SimpleNamespace(
            execution_id=context.execution_id,
            agent_id=request.agent_id,
            capability=request.capability,
            content="result",
        )


def make_context():
    metadata = {}
    events = []
    return SimpleNamespace(
        execution_id="exec-1",
        metadata=metadata,
        events=events,
        add_metadata=lambda key, value: metadata.__setitem__(key, value),
        add_event=lambda message, metadata=None: events.append(
            (message, metadata)
        ),
    )


@pytest.mark.asyncio
async def test_skill_execution_requires_compatible_agent():
    class IncompatibleManifest(FakeManifest):
        compatible_agents = ["project_manager"]

    execution = FakeExecutionService()
    service = SkillExecutionService(
        skill_registry=FakeRegistry(IncompatibleManifest()),
        agent_execution_service=execution,
    )

    request = SimpleNamespace(
        agent_id="platform_intelligence_agent",
        capability="platform_intelligence",
        validate_request=lambda: None,
    )

    with pytest.raises(PermissionError):
        await service.execute(
            skill_id="architecture_review",
            request=request,
            context=make_context(),
            skill_prompt="Review architecture.",
        )

    assert execution.called is False


@pytest.mark.asyncio
async def test_skill_execution_delegates_after_authorization():
    execution = FakeExecutionService()
    service = SkillExecutionService(
        skill_registry=FakeRegistry(),
        agent_execution_service=execution,
    )

    request = SimpleNamespace(
        agent_id="platform_intelligence_agent",
        capability="platform_intelligence",
        validate_request=lambda: None,
    )

    context = make_context()

    response = await service.execute(
        skill_id="architecture_review",
        request=request,
        context=context,
        skill_prompt="Review architecture.",
    )

    assert execution.called is True
    assert response.content == "result"
    assert context.metadata["skill_id"] == "architecture_review"
