"""
Speech Provider Configuration.

Defines provider settings required
for speech integrations.

Configuration only.

Does NOT:
- call providers
- store secrets directly
- execute speech operations
"""

from __future__ import annotations

from dataclasses import dataclass



@dataclass(
    frozen=True,
    slots=True,
)
class SpeechProviderConfig:
    """
    Immutable speech provider configuration.
    """

    provider_name: str

    model_name: str

    default_language: str

    enabled: bool = True


    def __post_init__(self) -> None:
        """
        Validate configuration.
        """

        if not self.provider_name.strip():
            raise ValueError(
                "provider_name cannot be empty."
            )

        if not self.model_name.strip():
            raise ValueError(
                "model_name cannot be empty."
            )

        if not self.default_language.strip():
            raise ValueError(
                "default_language cannot be empty."
            )