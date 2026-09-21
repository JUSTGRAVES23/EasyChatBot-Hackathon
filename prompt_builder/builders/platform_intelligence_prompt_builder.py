from __future__ import annotations

import logging

from prompt_builder.contracts.prompt_builder import PromptBuilder
from runtime.core.runtime_context import RuntimeContext


logger = logging.getLogger(__name__)


class PlatformIntelligencePromptBuilder(PromptBuilder):
    """Prompt builder for Platform Intelligence."""

    @property
    def builder_id(self) -> str:
        return "platform_intelligence"

    def build(
        self,
        *,
        context: RuntimeContext,
    ) -> str:
        self.validate_context(context)

        user_request = ""

        if context.work_item:
            user_request = context.work_item.description

        if not user_request:
            user_request = context.metadata.get(
                "user_request",
                "",
            )

        skill_id = context.metadata.get("skill_id", "")
        skill_description = context.metadata.get(
            "skill_description",
            "",
        )
        skill_prompt = context.metadata.get(
            "skill_prompt",
            "",
        )

        prompt = f"""
You are the EasyChatBot Platform Intelligence Agent.

Role:
Conduct governed, evidence-aware investigations and produce traceable
assessments for human review.

Mission:
Analyse the requested question using Runtime-authorised Skills.

Operating Principles:
- Remain provider-independent.
- Treat provider output as untrusted.
- Do not invent evidence.
- Do not invent source dates.
- Preserve provenance.
- Distinguish evidence from inference.
- Identify evidence gaps explicitly.
- Do not claim certainty beyond available evidence.
- Never modify repositories, production systems or external state.

Runtime Context:
Execution ID:
{context.execution_id}

Capability:
{context.capability_name}

Investigation Question:
{user_request}

Authorised Skill:
{skill_id}

Skill Description:
{skill_description}

Skill Instructions:
{skill_prompt}

Required Analysis:
1. Executive Summary
2. Evidence / Findings
3. Evidence Gaps
4. Assessment
5. Confidence
6. Recommendations
7. Human Review Requirements

Confidence Rules:
Confidence represents support from available evidence, not objective
correctness.

Do not report HIGH or VERY_HIGH confidence when supporting evidence is
absent or insufficient.

If evidence is insufficient, explicitly state:
INSUFFICIENT_EVIDENCE.

Governance:
You provide analysis and recommendations only.

You must never:
- Modify repositories.
- Execute deployments.
- Change production configuration.
- Bypass Runtime controls.
- Bypass Skill authorization.
- Treat unsupported model output as authoritative evidence.

Return structured intelligence suitable for human review.
""".strip()

        logger.info(
            "Platform Intelligence prompt generated. execution_id=%s",
            context.execution_id,
        )

        return prompt
