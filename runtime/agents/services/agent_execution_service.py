"""Provider-neutral governed Agent execution boundary.

This service owns execution orchestration only. Provider selection and SDK
access remain below the existing provider/application boundary.
"""
from __future__ import annotations

from typing import Any

from backend.conversation.conversation_request import ConversationRequest
from backend.services.llm_service import LLMService
from runtime.contracts.agent_execution_request import AgentExecutionRequest
from runtime.contracts.agent_execution_response import AgentExecutionResponse
from runtime.core.runtime_context import RuntimeContext


class AgentExecutionService:
    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    async def execute(
        self,
        request: AgentExecutionRequest,
        context: RuntimeContext,
    ) -> AgentExecutionResponse:
        if request is None:
            raise ValueError("request must not be None")
        if context is None:
            raise ValueError("context must not be None")

        context.capability_id = request.capability
        context.capability_name = request.capability
        context.work_item = request.instruction

        conversation = ConversationRequest(
            system_instruction=context.system_prompt or "",
            user_prompt=request.instruction,
            conversation_context=None,
        )

        result = self._llm_service.generate(conversation)

        if not result.success:
            error = result.error or "Provider execution failed"
            context.errors.append(error)
            return AgentExecutionResponse(
                execution_id=context.execution_id,
                agent_id=request.agent_id,
                capability=request.capability,
                success=False,
                error=error,
                metadata=dict(request.metadata),
            )

        context.raw_response = result.output
        context.parsed_response = result.output

        return AgentExecutionResponse(
            execution_id=context.execution_id,
            agent_id=request.agent_id,
            capability=request.capability,
            content=str(result.output or ""),
            success=True,
            metadata=dict(request.metadata),
        )
