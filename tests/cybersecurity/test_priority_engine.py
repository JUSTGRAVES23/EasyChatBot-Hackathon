from cybersecurity.decision_support.priority_engine import (
    CybersecurityPriorityEngine,
)


def test_critical_signal_receives_high_priority():

    engine = CybersecurityPriorityEngine()


    result = engine.calculate_priority(
        {
            "signal_id": "test-001",
            "title": "AI prompt injection attempt",
            "severity": "high",
            "category": "threat",
            "confidence": 0.96,
            "affected_area": "AI layer",
        }
    )


    assert result.priority.level in (
        "CRITICAL REVIEW",
        "HIGH REVIEW",
    )


    assert result.decision_required.startswith(
        "Human review"
    )

