from __future__ import annotations


class DeletionWorkflowService:
    """GDPR Article 17 erasure workflow orchestration.

    Deletes identifiable learner data while allowing only
    irreversible anonymised statistics to remain.
    """

    async def execute(self, learner_id: str) -> None:
        # Integration point:
        # account deletion
        # conversation deletion
        # memory deletion
        # learning portfolio deletion
        # community content deletion
        pass
