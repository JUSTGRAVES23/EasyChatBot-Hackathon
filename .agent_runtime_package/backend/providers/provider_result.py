"""
Provider Result Contract.

Defines the standard response returned
by external providers.

All providers return this structure so
the Runtime can process results consistently.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderResult:
    """
    Immutable provider execution result.

    Attributes:

        success:
            Indicates whether provider execution succeeded.

        provider_id:
            Identifier of the provider.

        output:
            Provider response payload.

        error:
            Error details if execution failed.
    """

    success: bool
    provider_id: str
    output: Any = None
    error: str | None = None