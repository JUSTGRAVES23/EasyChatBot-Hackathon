"""
Threat Prioritisation Skill.

Ranks already-analysed cybersecurity signals using
transparent deterministic criteria.

It does not:
- invent findings;
- make remediation decisions;
- call external providers;
- modify security state.
"""

from __future__ import annotations

from skills.skill import (
    Skill,
    SkillInput,
)

from skills.skill_result import (
    SkillResult,
)


class ThreatPrioritisationSkill(Skill):
    """
    Deterministically rank cybersecurity signals.
    """

    skill_id = (
        "cybersecurity.threat_prioritisation"
    )

    name = "Threat Prioritisation"

    version = "1.0.0"

    async def execute(
        self,
        skill_input: SkillInput,
    ) -> SkillResult:
        if skill_input is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="Skill input cannot be None.",
            )

        raw = skill_input.metadata.get(
            "analysed_signals"
        )

        if not isinstance(
            raw,
            (list, tuple),
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "analysed_signals must be "
                    "a list or tuple."
                ),
            )

        ranked = sorted(
            (
                item
                for item in raw
                if isinstance(item, dict)
            ),
            key=lambda item: (
                int(
                    item.get(
                        "severity_rank",
                        0,
                    )
                ),
                1 if item.get("is_open") else 0,
                float(
                    item.get(
                        "confidence",
                        0.0,
                    )
                ),
            ),
            reverse=True,
        )

        output: list[dict] = []

        for index, item in enumerate(
            ranked,
            start=1,
        ):
            output.append(
                {
                    "priority": index,
                    "signal": item.get("signal"),
                    "severity": item.get("severity"),
                    "confidence": item.get("confidence"),
                    "is_open": item.get("is_open"),
                }
            )

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output=output,
        )
