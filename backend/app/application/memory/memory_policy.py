from __future__ import annotations


from typing import Final


class MemoryPolicy:
    """
    Governance policy for learner memory.

    Application boundary.

    Responsibilities:

    - educational relevance validation
    - privacy minimisation
    - prevent unnecessary personal data retention

    Does NOT:

    - persist memory
    - approve memory
    - create learner profiles
    """



    ALLOWED_TYPES: Final = {
        "learning_progress",
        "grammar_mistake",
        "grammar_errors",
        "vocabulary",
        "vocabulary_gap",
        "pronunciation",
        "pronunciation_issue",
        "confidence",
        "confidence_level",
        "learning_preference",
        "communication_strength",
    }



    FORBIDDEN_TERMS: Final = {
        "email",
        "phone",
        "password",
        "passport",
        "address",
        "medical",
        "religion",
        "political",
        "financial",
    }



    def validate(
        self,
        *,
        memory_type: str | None = None,
        content: str | None = None,
        category: str | None = None,
        observation: str | None = None,
    ) -> bool:
        """
        Validate memory candidate.

        Supports:

        Current approval flow:

            memory_type
            content


        Legacy:

            category
            observation
        """



        normalized_type = (
            memory_type
            or category
            or ""
        )


        normalized_content = (
            content
            or observation
            or ""
        )



        if not normalized_type:

            raise ValueError(
                "Memory type required."
            )



        if normalized_type not in self.ALLOWED_TYPES:

            raise ValueError(
                f"Memory type not allowed: {normalized_type}"
            )



        lowered = normalized_content.lower()



        for term in self.FORBIDDEN_TERMS:

            if term in lowered:

                raise ValueError(
                    f"Forbidden personal information detected: {term}"
                )



        return True