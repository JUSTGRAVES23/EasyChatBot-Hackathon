"""
Executive Security Summary Skill.

Produces a concise decision-support summary from
prioritised supplied cybersecurity observations.

No external calls.
No fabricated data.
No remediation.
"""

from __future__ import annotations

from collections import Counter

from backend.skills.skill import (
    Skill,
    SkillInput,
)

from backend.skills.skill_result import (
    SkillResult,
)


class ExecutiveSecuritySummarySkill(Skill):
    """
    Convert prioritised security observations into a
    UI/API-safe executive summary.
    """

    skill_id = (
        "cybersecurity.executive_security_summary"
    )

    name = "Executive Security Summary"

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

        items = skill_input.metadata.get(
            "prioritised_signals"
        )

        if not isinstance(
            items,
            (list, tuple),
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "prioritised_signals must be "
                    "a list or tuple."
                ),
            )

        valid_items = [
            item
            for item in items
            if isinstance(item, dict)
        ]

        severities = Counter(
            str(
                item.get(
                    "severity",
                    "unknown",
                )
            ).lower()
            for item in valid_items
        )

        critical = severities.get(
            "critical",
            0,
        )

        high = severities.get(
            "high",
            0,
        )

        open_count = sum(
            1
            for item in valid_items
            if item.get("is_open")
        )

        if critical:
            posture = (
                "CRITICAL ATTENTION REQUIRED"
            )
        elif high:
            posture = (
                "HIGH ATTENTION REQUIRED"
            )
        elif open_count:
            posture = "MONITOR"
        else:
            posture = "NO OPEN SIGNALS"

        priorities: list[dict] = []

        for item in valid_items[:5]:
            signal = item.get("signal")

            if signal is None:
                continue

            priorities.append(
                {
                    "priority": item.get(
                        "priority"
                    ),
                    "signal_id": signal.signal_id,
                    "title": signal.title,
                    "category": signal.category,
                    "severity": signal.severity,
                    "confidence": signal.confidence,
                    "source": signal.source,
                    "affected_area": (
                        signal.affected_area
                    ),
                    "technique": signal.technique,
                    "status": signal.status,
                }
            )

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output={
                "posture": posture,
                "signal_count": len(valid_items),
                "open_signal_count": open_count,
                "critical_count": critical,
                "high_count": high,
                "medium_count": severities.get(
                    "medium",
                    0,
                ),
                "low_count": severities.get(
                    "low",
                    0,
                ),
                "priority_signals": priorities,
                "decision_note": (
                    "Review the highest-priority signals "
                    "and associated evidence. This output "
                    "is decision support only; no remediation "
                    "is executed."
                ),
                "execution_id": (
                    skill_input.metadata.get(
                        "execution_id"
                    )
                ),
            },
        )