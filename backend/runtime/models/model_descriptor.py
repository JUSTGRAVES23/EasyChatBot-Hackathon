"""
Model Descriptor.

Combines model identity and capabilities.

The Runtime uses this information
without depending on a specific provider.
"""

from dataclasses import dataclass

from backend.runtime.models.model_id import ModelId
from backend.runtime.models.model_capabilities import ModelCapabilities


@dataclass(frozen=True)
class ModelDescriptor:
    """
    Describes an available AI model.

    Attributes:

        model_id:
            Unique model identity.

        capabilities:
            Supported capabilities.

        description:
            Human-readable explanation.
    """

    model_id: ModelId

    capabilities: ModelCapabilities

    description: str = ""