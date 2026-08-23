"""
Security Signal Analysis Skill.

Deterministically validates and analyses supplied
cybersecurity signals.

Responsibilities:
- validate cybersecurity signals;
- calculate deterministic severity ranking;
- produce analysis metadata.

Does NOT:
- call external providers;
- modify security systems;
- execute remediation.
"""

from __future__ import annotations

from backend.cybersecurity.intelligence_models import (
    CybersecuritySignal,
)

from backend.skills.skill import (
    Skill,
    SkillInput,
)

from backend.skills.skill_result import (
    SkillResult,
)


class SecuritySignalAnalysisSkill(Skill):
    """
    Analyze normalized cybersecurity signals.
    """

    skill_id = (
        "cybersecurity.security_signal_analysis"
    )

    name = "Security Signal Analysis"

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
            "signals"
        )

        if not isinstance(
            raw,
            (list, tuple),
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "signals must be a list or tuple."
                ),
            )

        analysed: list[dict] = []

        for signal in raw:
            if not isinstance(
                signal,
                CybersecuritySignal,
            ):
                continue

            analysed.append(
                {
                    "signal": signal,
                    "severity": signal.severity,
                    "severity_rank": (
                        self._severity_rank(
                            signal.severity
                        )
                    ),
                    "confidence": signal.confidence,
                    "is_open": (
                        signal.status.strip().lower()
                        not in {
                            "closed",
                            "resolved",
                        }
                    ),
                }
            )

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output=analysed,
        )

    @staticmethod
    def _severity_rank(
        severity: str,
    ) -> int:
        return {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "info": 1,
        }.get(
            severity.strip().lower(),
            0,
        )