"""
Demo seed data for repeatable Operations Center recordings.
"""


CYBERSECURITY_DEMO_DATA = {
    "event": "CYBERSECURITY_ALERT",
    "component": "email_delivery",
    "severity": "CRITICAL",
    "reason": "External provider security incident",
    "actor": "Security Operations",
    "email": {
        "subject": "[DEMO] Critical Cybersecurity Alert",
        "status": "prepared",
    },
    "yeti_message": (
        "I detected a critical cybersecurity event. "
        "Email delivery governance controls were activated. "
        "Evidence is available."
    ),
}


PROVIDER_MANAGEMENT_DEMO_DATA = {
    "event": "PROVIDER_PAUSED",
    "component": "AI_PROVIDER",
    "severity": "CRITICAL",
    "reason": "Provider incident investigation",
    "actor": "Security Manager",
    "email": {
        "subject": "[DEMO] Provider Governance Change",
        "status": "prepared",
    },
    "yeti_message": (
        "A provider governance action has completed. "
        "The change was approved and evidence is available."
    ),
}
