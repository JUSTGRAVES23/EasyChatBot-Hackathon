"""
Cybersecurity Decision Support Agent.

Reads cybersecurity intelligence and produces
human decision-support information.
"""

from __future__ import annotations


from cybersecurity.decision_support.priority_engine import (
    CybersecurityPriorityEngine,
)

from cybersecurity.decision_support.agent.models import (
    CybersecurityDecisionBrief,
    DecisionBriefItem,
)



class CybersecurityDecisionSupportAgent:


    agent_id = (
        "cybersecurity.decision_support"
    )


    def __init__(self):

        self.priority_engine = (
            CybersecurityPriorityEngine()
        )


    async def analyse(
        self,
        intelligence: dict,
    ) -> CybersecurityDecisionBrief:


        signals = intelligence.get(
            "signals",
            []
        )


        decisions = []


        for signal in signals:

            priority_result = (
                self.priority_engine
                .calculate_priority(
                    signal
                )
            )


            decisions.append(

                DecisionBriefItem(

                    title=
                    priority_result.title,

                    priority=
                    priority_result.priority.level,

                    severity=
                    priority_result.severity,

                    impact=(

                        f"Potential impact "
                        f"on "
                        f"{priority_result.affected_area}."

                    ),

                    affected_area=
                    priority_result.affected_area,

                    decision_required=
                    priority_result.decision_required,

                )

            )


        critical = [

            item for item in decisions

            if item.priority ==
            "CRITICAL REVIEW"

        ]


        high = [

            item for item in decisions

            if item.priority ==
            "HIGH REVIEW"

        ]



        if critical:

            overall = "CRITICAL REVIEW REQUIRED"

        elif high:

            overall = "HIGH REVIEW REQUIRED"

        else:

            overall = "MONITOR"



        return CybersecurityDecisionBrief(

            executive_summary=(

                f"Cybersecurity intelligence "
                f"review completed. "

                f"{len(decisions)} "
                f"signals analysed."

            ),

            overall_priority=overall,

            critical_items=critical,

            high_priority_items=high,

            governance_observations=[

                "Human review required for "
                "security and AI governance matters."

            ],

            trend_analysis=(

                "Trend analysis requires "
                "historical intelligence data."

            ),

            recommended_decisions=[

                "Review highest priority "
                "security matters.",

                "Confirm ownership and "
                "next review actions."

            ],

        )

