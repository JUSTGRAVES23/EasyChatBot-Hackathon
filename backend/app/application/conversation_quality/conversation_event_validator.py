from __future__ import annotations

from typing import Any


class ConversationEventValidator:
    """
    Validates conversation events before persistence.

    Governance controls:

    - no raw identity
    - no injected learner context
    - metadata completeness
    - retention classification

    Used before:
    
        ConversationEventRepository.save()

    """

    REQUIRED_METADATA = {
        "world_id",
        "character",
        "level",
        "source",
        "retention_policy_id",
    }


    FORBIDDEN_CONTENT = {
        "email:",
        "user:",
        "telegram_user_id",
        "beta learner context",
        "david@example.com",
    }


    def validate(
        self,
        *,
        content: str,
        metadata: dict[str, Any] | None,
        telegram_user_hash: str,
    ) -> dict[str, Any]:

        if not telegram_user_hash:
            raise ValueError(
                "Conversation event requires pseudonymous identity."
            )


        if not content:
            raise ValueError(
                "Conversation content cannot be empty."
            )


        lowered = content.lower()


        for item in self.FORBIDDEN_CONTENT:

            if item.lower() in lowered:

                raise ValueError(
                    f"Forbidden personal context detected: {item}"
                )


        if metadata is None:

            raise ValueError(
                "Conversation metadata missing."
            )


        missing = (
            self.REQUIRED_METADATA
            -
            metadata.keys()
        )


        if missing:

            raise ValueError(
                f"Missing metadata: {missing}"
            )


        return {
            "valid": True,
            "checks": {
                "identity_protection": True,
                "metadata_complete": True,
                "retention_classified": True,
            },
        }