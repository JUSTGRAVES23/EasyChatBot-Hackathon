"""
Model Identifier.

Defines a stable identifier for AI models.

The identifier is independent from provider execution logic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelId:
    """
    Unique identifier for an AI model.

    Examples:

    gemini-2.5-flash
    gpt-5-mini
    llama3

    """

    provider: str
    name: str

    def full_name(self) -> str:
        """
        Returns the complete model identifier.
        """

        return f"{self.provider}:{self.name}"