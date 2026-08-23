class CybersecurityDemoService:

    def create_incident(self):

        return {
            "event": "CYBERSECURITY_ALERT",
            "component": "email_delivery",
            "severity": "CRITICAL",
            "reason": "External provider security incident",
        }
