"""
AI Runtime capability errors.

These exceptions provide explicit Runtime-level failure semantics.

The Runtime must distinguish between:

- invalid requests
- unknown capabilities
- duplicate capability registration
- governance rejection
- capability execution failure

Provider-specific exceptions must not leak through the Runtime
boundary.
"""

from __future__ import annotations


class RuntimeCapabilityError(Exception):
    """
    Base exception for Runtime capability failures.
    """


class InvalidCapabilityRequestError(
    RuntimeCapabilityError
):
    """
    Raised when a capability request is invalid.
    """


class CapabilityNotRegisteredError(
    RuntimeCapabilityError
):
    """
    Raised when no executor is registered for a capability.
    """


class CapabilityAlreadyRegisteredError(
    RuntimeCapabilityError
):
    """
    Raised when an executor is registered more than once.
    """


class CapabilityExecutionError(
    RuntimeCapabilityError
):
    """
    Raised when a capability executor fails during execution.

    The original provider/implementation exception is retained
    as the exception cause, but callers receive a Runtime-level
    error type.
    """


class CapabilityGovernanceError(
    RuntimeCapabilityError
):
    """
    Raised when governance evaluation itself fails.

    This is deliberately different from a governance rejection.

    Rejection:
        governance worked and said no.

    Governance error:
        governance could not produce a valid decision.
    """