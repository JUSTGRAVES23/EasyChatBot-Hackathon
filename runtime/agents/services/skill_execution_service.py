from __future__ import annotations

import logging

from runtime.agents.services.agent_execution_service import AgentExecutionService
from runtime.agents.services.source_skill_executor import SourceSkillExecutor
from runtime.capabilities.registries.skill_registry import SkillRegistry
from runtime.contracts.agent_execution_request import AgentExecutionRequest
from runtime.contracts.agent_execution_response import AgentExecutionResponse
from runtime.core.runtime_context import RuntimeContext


logger = logging.getLogger(__name__)


class SkillExecutionService:
    """
    Runtime-controlled execution boundary for Skills.

    Authorization is reusable independently from direct Skill execution.

    Skill manifests may use governed agent aliases for compatibility.
    Canonical Runtime agent IDs remain authoritative internally.

    Analysis Skills are delegated to AgentExecutionService. Source Skills are
    delegated to SourceSkillExecutor so source-grounded Evidence is produced
    without crossing the provider boundary.
    """

    AGENT_COMPATIBILITY_ALIASES: dict[str, tuple[str, ...]] = {
        "project_manager": ("aurelius",),
        "platform_intelligence_agent": ("romanoide",),
    }

    def __init__(
        self,
        *,
        skill_registry: SkillRegistry,
        agent_execution_service: AgentExecutionService,
        source_skill_executor: SourceSkillExecutor | None = None,
    ) -> None:
        if skill_registry is None:
            raise ValueError("SkillRegistry cannot be None.")

        if agent_execution_service is None:
            raise ValueError("AgentExecutionService cannot be None.")

        self._skill_registry = skill_registry
        self._agent_execution_service = agent_execution_service
        self._source_skill_executor = (
            source_skill_executor or SourceSkillExecutor()
        )

        logger.info("SkillExecutionService initialised.")

    @classmethod
    def _agent_is_compatible(
        cls,
        *,
        agent_id: str,
        compatible_agents: tuple[str, ...] | list[str],
    ) -> bool:
        """Determine whether a canonical Runtime agent is authorised."""
        if agent_id in compatible_agents:
            return True

        aliases = cls.AGENT_COMPATIBILITY_ALIASES.get(agent_id, ())

        return any(alias in compatible_agents for alias in aliases)

    def authorize(
        self,
        *,
        skill_id: str,
        agent_id: str,
        context: RuntimeContext,
    ):
        """
        Resolve and authorize a Skill for an Agent.

        This method performs governance and Runtime-context enrichment only.
        It does not execute the Agent or call a provider.
        """
        if not isinstance(skill_id, str) or not skill_id.strip():
            raise ValueError("skill_id cannot be empty.")

        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id cannot be empty.")

        if context is None:
            raise ValueError("RuntimeContext cannot be None.")

        manifest = self._skill_registry.get(skill_id)

        if manifest is None:
            raise KeyError(f"Skill '{skill_id}' is not registered.")

        manifest.validate()

        if manifest.status.lower() != "active":
            raise PermissionError(
                f"Skill '{skill_id}' is not active and cannot be executed."
            )

        if manifest.compatible_agents:
            if not self._agent_is_compatible(
                agent_id=agent_id,
                compatible_agents=manifest.compatible_agents,
            ):
                raise PermissionError(
                    f"Agent '{agent_id}' is not authorised "
                    f"to execute Skill '{skill_id}'."
                )

        context.add_metadata("skill_id", manifest.id)
        context.add_metadata("skill_name", manifest.name)
        context.add_metadata("skill_description", manifest.description)
        context.add_metadata(
            "skill_prompt",
            self._skill_registry.load_prompt(manifest.id),
        )
        context.add_metadata("skill_version", manifest.version)
        context.add_metadata("skill_status", manifest.status)
        context.add_metadata("skill_owner", manifest.owner)
        context.add_metadata("skill_category", manifest.category)
        context.add_metadata("skill_execution_mode", "read_only")

        context.add_event(
            "Runtime Skill authorization validated.",
            metadata={
                "skill_id": manifest.id,
                "agent_id": agent_id,
            },
        )

        logger.info(
            "Runtime Skill authorization validated. skill=%s agent=%s execution_id=%s",
            manifest.id,
            agent_id,
            context.execution_id,
        )

        return manifest

    async def execute(
        self,
        *,
        skill_id: str,
        request: AgentExecutionRequest,
        context: RuntimeContext,
    ) -> AgentExecutionResponse:
        """Execute a Runtime-authorised Skill."""
        if request is None:
            raise ValueError("AgentExecutionRequest cannot be None.")

        if context is None:
            raise ValueError("RuntimeContext cannot be None.")

        request.validate_request()

        manifest = self.authorize(
            skill_id=skill_id,
            agent_id=request.agent_id,
            context=context,
        )

        logger.info(
            "Executing governed Skill. skill=%s agent=%s execution_id=%s",
            manifest.id,
            request.agent_id,
            context.execution_id,
        )

        if manifest.category.lower() == "source":
            response = await self._source_skill_executor.execute(
                skill_id=manifest.id,
                request=request,
                context=context,
            )
        else:
            response = await self._agent_execution_service.execute(
                request=request,
                context=context,
            )

        if response is None:
            raise RuntimeError("Skill execution returned no response.")

        context.add_event(
            "Runtime Skill execution completed.",
            metadata={
                "skill_id": manifest.id,
                "agent_id": request.agent_id,
                "skill_category": manifest.category,
            },
        )

        return response
