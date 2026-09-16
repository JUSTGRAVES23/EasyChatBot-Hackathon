"""
Tests for Cybersecurity Email Generator.
"""

from cybersecurity.cybersecurity_email_generator import (
    CybersecurityEmailGenerator,
)



def test_generate_critical_alert_email():

    generator = CybersecurityEmailGenerator()


    result = generator.generate_critical_alert(
        {
            "posture":
                "CRITICAL ATTENTION REQUIRED",

            "critical_count":
                1,

            "high_count":
                2,

            "priority_signals":
                [
                    {
                        "title":
                            "Critical vulnerability",
                    }
                ],
        }
    )


    assert result["priority"] == "critical"

    assert (
        result["recipient"]
        ==
        "davdbarbero1999@gmail.com"
    )

    assert (
        "CRITICAL"
        in result["subject"]
    )

