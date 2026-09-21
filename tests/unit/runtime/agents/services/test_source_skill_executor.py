from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from runtime.agents.services.source_skill_executor import SourceSkillExecutor
from runtime.contracts.agent_execution_request import AgentExecutionRequest
from runtime.contracts.evidence import Evidence
from runtime.core.runtime_context import RuntimeContext


def make_context() -> RuntimeContext:
    return RuntimeContext.model_construct(
        execution_id="exec-001",
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


def make_request(context: dict) -> AgentExecutionRequest:
    return AgentExecutionRequest(
        agent_id="platform_intelligence_agent",
        capability="repository_reader",
        instruction="Read the supplied repository source.",
        context=context,
        metadata={},
    )


@pytest.mark.asyncio
async def test_source_skill_executor_creates_canonical_evidence():
    runtime_context = make_context()
    source = "class Example:\n    pass\n"
    request = make_request(
        {
            "source_code": source,
            "source_path": "runtime/example.py",
        }
    )

    response = await SourceSkillExecutor().execute(
        skill_id="repository_reader",
        request=request,
        context=runtime_context,
    )

    assert response.success is True
    assert response.structured_output["evidence"]

    evidence = response.structured_output["evidence"][0]
    assert isinstance(evidence, Evidence)
    assert evidence.content == source
    assert evidence.source == "repository"
    assert evidence.source_type == "repository"
    assert evidence.authority == "AUTHORITATIVE"
    assert evidence.location == "runtime/example.py"
    assert evidence.metadata["skill_id"] == "repository_reader"
    assert evidence.metadata["provenance"] == "runtime_supplied_source"

    assert runtime_context.artifacts["evidence"] == (evidence,)


@pytest.mark.asyncio
async def test_source_skill_executor_reads_only_runtime_supplied_source():
    runtime_context = make_context()
    source = "print('governed input')"
    runtime_context.add_artifact(
        "source_input",
        {
            "source_code": source,
            "source_path": "app/example.py",
        },
    )

    request = make_request({})

    response = await SourceSkillExecutor().execute(
        skill_id="repository_reader",
        request=request,
        context=runtime_context,
    )

    evidence = response.structured_output["evidence"][0]
    assert evidence.content == source
    assert evidence.location == "app/example.py"


@pytest.mark.asyncio
async def test_source_skill_executor_rejects_missing_source():
    runtime_context = make_context()
    request = make_request({})

    with pytest.raises(ValueError, match="No governed source input"):
        await SourceSkillExecutor().execute(
            skill_id="repository_reader",
            request=request,
            context=runtime_context,
        )


@pytest.mark.asyncio
async def test_source_skill_executor_rejects_empty_source_code():
    runtime_context = make_context()
    request = make_request({"source_code": "   "})

    with pytest.raises(ValueError, match="non-empty 'source_code'"):
        await SourceSkillExecutor().execute(
            skill_id="repository_reader",
            request=request,
            context=runtime_context,
        )


@pytest.mark.asyncio
async def test_source_skill_executor_does_not_require_provider():
    runtime_context = make_context()
    request = make_request({"source_code": "value = 1"})

    response = await SourceSkillExecutor().execute(
        skill_id="repository_reader",
        request=request,
        context=runtime_context,
    )

    assert response.metadata["execution_mode"] == "read_only"
    assert runtime_context.provider_id == ""
    assert runtime_context.model_name == ""
