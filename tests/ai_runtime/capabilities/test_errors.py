"""
Tests for Runtime capability errors.
"""

from src.ai_runtime.capabilities.errors import (
    CapabilityAlreadyRegisteredError,
    CapabilityExecutionError,
    CapabilityGovernanceError,
    CapabilityNotRegisteredError,
    InvalidCapabilityRequestError,
    RuntimeCapabilityError,
)


def test_all_runtime_errors_extend_runtime_capability_error():

    errors = (
        InvalidCapabilityRequestError,
        CapabilityNotRegisteredError,
        CapabilityAlreadyRegisteredError,
        CapabilityExecutionError,
        CapabilityGovernanceError,
    )

    for error_type in errors:
        assert issubclass(
            error_type,
            RuntimeCapabilityError,
        )