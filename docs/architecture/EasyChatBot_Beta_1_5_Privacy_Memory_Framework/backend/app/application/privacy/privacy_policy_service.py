class PrivacyPolicyService:
    def validate_retention(self, policy_id: str) -> bool:
        return bool(policy_id)
