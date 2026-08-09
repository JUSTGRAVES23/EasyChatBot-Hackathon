"""
Model Capability Definition.

Describes what an AI model can support.

Used by the Runtime to select appropriate models.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelCapabilities:
    """
    Capabilities supported by a model.
    """

    text_generation: bool = True
    reasoning: bool = False
    tool_usage: bool = False
    vision: bool = False
    audio: bool = False