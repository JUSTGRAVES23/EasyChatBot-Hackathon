"""
Cybersecurity Decision Priority Engine.

Responsible for ranking cybersecurity intelligence.

It does NOT:
- remediate issues;
- close findings;
- change systems;
- make operational decisions.

It only supports human review.
"""

from __future__ import annotations

from cybersecurity.decision_support.models import (
    DecisionPriority,
    SecurityDecisionItem,
)


class CybersecurityPriorityEngine:


    def calculate_priority(
        self,
        signal: dict,
    ) -> SecurityDecisionItem:


        severity = (
            signal.get(
                "severity",
                "low"
            )
            .lower()
        )


        confidence = float(
            signal.get(
                "confidence",
                0
            )
        )


        category = signal.get(
            "category",
            "unknown"
        )


        score = 0


        #
        # Severity weighting
        #

        if severity == "critical":
            score += 100

        elif severity == "high":
            score += 75

        elif severity == "medium":
            score += 50

        else:
            score += 25



        #
        # Confidence weighting
        #

        if confidence >= 0.95:
            score += 20

        elif confidence >= 0.80:
            score += 10



        #
        # Governance / AI specific sensitivity
        #

        if category in (
            "threat",
            "governance",
            "identity",
        ):
            score += 10



        if score >= 120:

            level = "CRITICAL REVIEW"

        elif score >= 80:

            level = "HIGH REVIEW"

        elif score >= 50:

            level = "MEDIUM REVIEW"

        else:

            level = "LOW REVIEW"



        rationale = (

            f"Priority calculated from "
            f"severity={severity}, "
            f"confidence={confidence}, "
            f"category={category}."

        )


        return SecurityDecisionItem(

            signal_id=signal["signal_id"],

            title=signal["title"],

            severity=severity,

            category=category,

            affected_area=
                signal.get(
                    "affected_area",
                    "unknown",
                ),

            confidence=confidence,

            priority=DecisionPriority(

                level=level,

                score=score,

                rationale=rationale,

            ),

            decision_required=(

                "Human review required. "
                "No automated action executed."

            ),

        )

