"""
Cybersecurity Intelligence Agent.

Agent 1 for the EasyChatBot Cybersecurity Operations Center.

Responsibilities:
- analyse supplied cybersecurity signals;
- orchestrate cybersecurity intelligence skills;
- produce provider-independent decision support.

Does NOT:
- call provider SDKs directly;
- modify production systems;
- execute remediation;
- send emails;
- persist security state.
"""

from __future__ import annotations

from backend.agents.agent_result import (
    AgentResult,
)

from backend.agents.base_agent import (
    BaseAgent,
)

from backend.cybersecurity.intelligence_models import (
    CybersecuritySignal,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)

from backend.skills.skill import (
    SkillInput,
)

from backend.skills.cybersecurity.executive_security_summary import (
    ExecutiveSecuritySummarySkill,
)

from backend.skills.cybersecurity.security_signal_analysis import (
    SecuritySignalAnalysisSkill,
)

from backend.skills.cybersecurity.threat_prioritisation import (
    ThreatPrioritisationSkill,
)


class CybersecurityIntelligenceAgent(BaseAgent):
    """
    Stateless Cybersecurity Intelligence Agent.

    Security observations are supplied through the
    ExecutionContext metadata.
    """

    agent_id = "cybersecurity.intelligence"

    name = "Cybersecurity Intelligence Agent"

    version = "1.0.0"

    def __init__(
        self,
        signal_analysis_skill: (
            SecuritySignalAnalysisSkill | None
        ) = None,
        prioritisation_skill: (
            ThreatPrioritisationSkill | None
        ) = None,
        summary_skill: (
            ExecutiveSecuritySummarySkill | None
        ) = None,
    ) -> None:

        self._signal_analysis = (
            signal_analysis_skill
            or SecuritySignalAnalysisSkill()
        )

        self._prioritisation = (
            prioritisation_skill
            or ThreatPrioritisationSkill()
        )

        self._summary = (
            summary_skill
            or ExecutiveSecuritySummarySkill()
        )

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        """
        Analyse supplied cybersecurity signals.
        """

        if context is None:
            return AgentResult(
                success=False,
                agent_id=self.agent_id,
                output=None,
                error=(
                    "Execution context cannot be None."
                ),
            )

        raw_signals = context.metadata.get(
            "cybersecurity_signals"
        )

        if raw_signals is None:
            return AgentResult(
                success=False,
                agent_id=self.agent_id,
                output=None,
                error=(
                    "cybersecurity_signals are required "
                    "in execution metadata."
                ),
            )

        if not isinstance(
            raw_signals,
            (list, tuple),
        ):
            return AgentResult(
                success=False,
                agent_id=self.agent_id,
                output=None,
                error=(
                    "cybersecurity_signals must be "
                    "a list or tuple."
                ),
            )

        signals = [
            item
            for item in raw_signals
            if isinstance(
                item,
                CybersecuritySignal,
            )
        ]

        analysis_result = await (
            self._signal_analysis.execute(
                SkillInput(
                    request=context.request,
                    metadata={
                        "signals": signals,
                    },
                )
            )
        )

        if not analysis_result.success:
            return AgentResult(
                success=False,
                agent_id=self.agent_id,
                output=None,
                error=(
                    analysis_result.error
                    or "Signal analysis failed."
                ),
            )

        prioritisation_result = await (
            self._prioritisation.execute(
                SkillInput(
                    request=context.request,
                    metadata={
                        "analysed_signals": (
                            analysis_result.output
                        ),
                    },
                )
            )
        )

        if not prioritisation_result.success:
            return AgentResult(
                success=False,
                agent_id=self.agent_id,
                output=None,
                error=(
                    prioritisation_result.error
                    or "Threat prioritisation failed."
                ),
            )

        summary_result = await (
            self._summary.execute(
                SkillInput(
                    request=context.request,
                    metadata={
                        "prioritised_signals": (
                            prioritisation_result.output
                        ),
                        "execution_id": (
                            context.execution_id
                        ),
                    },
                )
            )
        )

        if not summary_result.success:
            return AgentResult(
                success=False,
                agent_id=self.agent_id,
                output=None,
                error=(
                    summary_result.error
                    or "Executive summary failed."
                ),
            )

        summary = summary_result.output

        if not isinstance(summary, dict):
            return AgentResult(
                success=False,
                agent_id=self.agent_id,
                output=None,
                error=(
                    "Executive security summary "
                    "returned an invalid output."
                ),
            )

        return AgentResult(
            success=True,
            agent_id=self.agent_id,
            output={
                # Primary API/UI contract.
                "signal_count": summary.get(
                    "signal_count",
                    0,
                ),
                "open_signal_count": summary.get(
                    "open_signal_count",
                    0,
                ),
                "critical_count": summary.get(
                    "critical_count",
                    0,
                ),
                "high_count": summary.get(
                    "high_count",
                    0,
                ),
                "medium_count": summary.get(
                    "medium_count",
                    0,
                ),
                "low_count": summary.get(
                    "low_count",
                    0,
                ),
                "posture": summary.get(
                    "posture",
                    "UNKNOWN",
                ),
                "priority_signals": summary.get(
                    "priority_signals",
                    [],
                ),
                "decision_note": summary.get(
                    "decision_note",
                    "",
                ),
                "execution_id": summary.get(
                    "execution_id"
                ),

                # Internal diagnostic information.
                "analysis": analysis_result.output,
                "prioritised_signals": (
                    prioritisation_result.output
                ),
            },
        )