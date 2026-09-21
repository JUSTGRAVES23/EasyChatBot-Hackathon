from __future__ import annotations

from types import SimpleNamespace

from prompt_builder.builders.platform_intelligence_prompt_builder import (
    PlatformIntelligencePromptBuilder,
)


def test_platform_intelligence_builder_id() -> None:
    builder = PlatformIntelligencePromptBuilder()
    assert builder.builder_id == "platform_intelligence"


def test_platform_intelligence_prompt_contains_skill_contract() -> None:
    builder = PlatformIntelligencePromptBuilder()

    context = SimpleNamespace(
        execution_id="exec-1",
        capability_name="Platform Intelligence",
        work_item=SimpleNamespace(
            description="Review the architecture."
        ),
        metadata={
            "skill_id": "architecture_review",
            "skill_description": "Architecture review.",
            "skill_prompt": "Review architecture and recommend improvements.",
        },
    )

    prompt = builder.build(context=context)

    assert "architecture_review" in prompt
    assert "Architecture review." in prompt
    assert "Review architecture" in prompt
    assert "INSUFFICIENT_EVIDENCE" in prompt
