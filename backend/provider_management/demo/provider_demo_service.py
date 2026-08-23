class ProviderManagementDemoService:

    def create_provider_change(self):

        return {
            "event": "PROVIDER_PAUSED",
            "component": "AI_PROVIDER",
            "severity": "CRITICAL",
            "reason": "Provider incident investigation",
        }
