from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from runtime.agents.services.skill_execution_service import SkillExecutionService
from runtime.contracts.agent_execution_request import AgentExecutionRequest
from runtime.core.runtime_context import RuntimeContext


def make_context() -> RuntimeContext:
    return RuntimeContext.model_construct(
        execution_id="exec-routing-001",
        pipeline_name="test",
        capability_id="platform_intelligence",
        capability_name="Platform Intelligence",
        work_item=MagicMock(),
        system_prompt="",
        rendered_prompt="",
        provider_id="",
        model_name="",
        raw_response="",
        parsed_response=None,
        memory={},
        artifacts={},
        metrics={},
        metadata={},
        events=[],
        warnings=[],
        errors=[],
    )


def make_request() -> AgentExecutionRequest:
    return AgentExecutionRequest(
        agent_id="platform_intelligence_agent",
        capability="repository_reader",
        instruction="Read source.",
        context={"source_code": "value = 1", "source_path": "app.py"},
        metadata={},
    )


def make_manifest(category: str):
    manifest = MagicMock()
    manifest.id = "repository_reader" if category == "source" else "architecture_review"
    manifest.name = "Repository Reader" if category == "source" else "Architecture Review"
    manifest.description = "Test skill"
    manifest.version = "1.0.0"
    manifest.status = "active"
    manifest.owner = "AI Engineering Runtime"
    manifest.category = category
    manifest.compatible_agents = ("romanoide",)
    manifest.validate.return_value = None
    return manifest


@pytest.mark.asyncio
async def test_source_skill_routes_to_source_executor_not_llm():
    registry = MagicMock()
    registry.get.return_value = make_manifest("source")
    registry.load_prompt.return_value = "source prompt"

    agent_execution_service = MagicMock()
    agent_execution_service.execute = AsyncMock()

    source_executor = MagicMock()
    source_response = MagicMock()
    source_response.success = True
    source_executor.execute = AsyncMock(return_value=source_response)

    service = SkillExecutionService(
        skill_registry=registry,
        agent_execution_service=agent_execution_service,
        source_skill_executor=source_executor,
    )

    response = await service.execute(
        skill_id="repository_reader",
        request=make_request(),
        context=make_context(),
    )

    assert response is source_response
    source_executor.execute.assert_awaited_once()
    agent_execution_service.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_analysis_skill_keeps_existing_agent_execution_path():
    registry = MagicMock()
    registry.get.return_value = make_manifest("analysis")
    registry.load_prompt.return_value = "analysis prompt"

    agent_execution_service = MagicMock()
    response = MagicMock()
    response.success = True
    agent_execution_service.execute = AsyncMock(return_value=response)

    source_executor = MagicMock()
    source_executor.execute = AsyncMock()

    service = SkillExecutionService(
        skill_registry=registry,
        agent_execution_service=agent_execution_service,
        source_skill_executor=source_executor,
    )

    request = make_request()
    request = request.model_copy(update={"capability": "architecture_review"})

    result = await service.execute(
        skill_id="architecture_review",
        request=request,
        context=make_context(),
    )

    assert result is response
    agent_execution_service.execute.assert_awaited_once()
    source_executor.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_source_skill_still_requires_authorization():
    registry = MagicMock()
    manifest = make_manifest("source")
    manifest.compatible_agents = ("some_other_agent",)
    registry.get.return_value = manifest
    registry.load_prompt.return_value = "source prompt"

    source_executor = MagicMock()
    source_executor.execute = AsyncMock()

    service = SkillExecutionService(
        skill_registry=registry,
        agent_execution_service=MagicMock(),
        source_skill_executor=source_executor,
    )

    with pytest.raises(PermissionError, match="not authorised"):
        await service.execute(
            skill_id="repository_reader",
            request=make_request(),
            context=make_context(),
        )

    source_executor.execute.assert_not_awaited()
