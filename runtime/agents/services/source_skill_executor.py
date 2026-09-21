from __future__ import annotations

import logging
from typing import Any

from runtime.contracts.agent_execution_request import AgentExecutionRequest
from runtime.contracts.agent_execution_response import AgentExecutionResponse
from runtime.contracts.evidence import Evidence
from runtime.core.runtime_context import RuntimeContext


logger = logging.getLogger(__name__)


class SourceSkillExecutor:
    """
    Runtime-controlled executor for governed source Skills.

    Source Skills are deliberately kept outside the LLM/provider execution
    boundary. The executor consumes source material that has already been
    supplied through the Runtime execution context and converts that material
    into canonical Evidence.

    This class does not:
    - discover repositories or files;
    - access databases or external systems;
    - call an LLM/provider;
    - select a provider/model;
    - modify source systems;
    - perform authorization itself.

    Authorization remains the responsibility of SkillExecutionService and
    must occur before this executor is invoked.
    """

    SOURCE_INPUT_ARTIFACT = "source_input"

    def __init__(self) -> None:
        logger.info("SourceSkillExecutor initialised.")

    async def execute(
        self,
        *,
        skill_id: str,
        request: AgentExecutionRequest,
        context: RuntimeContext,
    ) -> AgentExecutionResponse:
        """Execute an already-authorized source Skill from supplied input."""

        if not isinstance(skill_id, str) or not skill_id.strip():
            raise ValueError("skill_id cannot be empty.")

        if request is None:
            raise ValueError("AgentExecutionRequest cannot be None.")

        if context is None:
            raise ValueError("RuntimeContext cannot be None.")

        request.validate_request()

        source_input = self._resolve_source_input(
            request=request,
            context=context,
        )

        source_code = source_input.get("source_code")
        if not isinstance(source_code, str) or not source_code.strip():
            raise ValueError(
                "Source Skill execution requires non-empty 'source_code'."
            )

        source_path = source_input.get("source_path", "")
        if source_path is None:
            source_path = ""
        if not isinstance(source_path, str):
            raise TypeError("source_path must be a string when supplied.")

        evidence = Evidence(
            evidence_id=(
                f"{context.execution_id}:"
                f"{skill_id}:source"
            ),
            source="repository",
            source_type="repository",
            authority="AUTHORITATIVE",
            content=source_code,
            location=source_path,
            metadata={
                "skill_id": skill_id,
                "agent_id": request.agent_id,
                "execution_id": str(context.execution_id),
                "provenance": "runtime_supplied_source",
            },
        )
        evidence.validate()

        context.add_artifact(
            "evidence",
            (evidence,),
        )
        context.add_event(
            "Governed source Skill produced Evidence.",
            metadata={
                "skill_id": skill_id,
                "agent_id": request.agent_id,
                "evidence_id": evidence.evidence_id,
            },
        )

        logger.info(
            (
                "Governed source Skill executed. skill=%s agent=%s "
                "execution_id=%s evidence_id=%s"
            ),
            skill_id,
            request.agent_id,
            context.execution_id,
            evidence.evidence_id,
        )

        return AgentExecutionResponse(
            execution_id=context.execution_id,
            agent_id=request.agent_id,
            capability=request.capability,
            content=(
                f"Source Skill '{skill_id}' produced "
                f"{len((evidence,))} evidence record."
            ),
            structured_output={
                "evidence": [evidence],
            },
            success=True,
            error=None,
            metadata={
                "skill_id": skill_id,
                "execution_mode": "read_only",
                "evidence_count": 1,
            },
        )

    @classmethod
    def _resolve_source_input(
        cls,
        *,
        request: AgentExecutionRequest,
        context: RuntimeContext,
    ) -> dict[str, Any]:
        """
        Resolve source input already present in the Runtime boundary.

        Request context takes precedence because it is the explicit input of
        the Skill execution. Runtime artifacts provide the canonical pipeline
        hand-off when the source was attached by an earlier stage.
        """

        request_source = request.context.get(cls.SOURCE_INPUT_ARTIFACT)
        if request_source is None:
            request_source = request.context

        if request_source:
            if not isinstance(request_source, dict):
                raise TypeError("source_input must be a mapping.")
            if "source_code" in request_source:
                return dict(request_source)

        artifact_source = context.artifacts.get(cls.SOURCE_INPUT_ARTIFACT)
        if artifact_source is None:
            raise ValueError(
                "No governed source input was supplied in the Runtime context."
            )

        if not isinstance(artifact_source, dict):
            raise TypeError("Runtime source_input artifact must be a mapping.")

        return dict(artifact_source)
