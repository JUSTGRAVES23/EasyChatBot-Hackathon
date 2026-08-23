class GovernanceChangeLifecycleViewModel:

    def build(self, change):
        return {
            "change_id": change.change_id,
            "component": change.component,
            "action": change.action,
            "risk": change.risk.value,
            "status": change.status.value,
        }
