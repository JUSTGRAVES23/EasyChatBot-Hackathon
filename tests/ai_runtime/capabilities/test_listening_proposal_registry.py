"""
Tests for Podcast Listening Proposal capability registration.
"""

import pytest

from src.ai_runtime.capabilities.errors import (
    CapabilityAlreadyRegisteredError,
    CapabilityNotRegisteredError,
)

from src.ai_runtime.capabilities.listening_proposal_executor import (
    ListeningProposalExecutor,
)

from src.ai_runtime.capabilities.models import (
    CapabilityType,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)


def test_registry_registers_listening_proposal_executor():
    """
    Verify that the Listening Proposal executor can be
    registered with the Runtime capability registry.
    """

    executor = ListeningProposalExecutor()

    registry = CapabilityRegistry()

    registry.register(
        executor,
    )

    assert registry.contains(
        CapabilityType.PODCAST_LISTENING_PROPOSAL,
    )


def test_registry_resolves_listening_proposal_executor():
    """
    Verify that the registry resolves the exact executor
    registered for Podcast Listening Proposal.
    """

    executor = ListeningProposalExecutor()

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    resolved = registry.resolve(
        CapabilityType.PODCAST_LISTENING_PROPOSAL,
    )

    assert resolved is executor


def test_registry_contains_listening_proposal_capability():
    """
    Verify contains() returns True after registration.
    """

    executor = ListeningProposalExecutor()

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    assert (
        registry.contains(
            CapabilityType.PODCAST_LISTENING_PROPOSAL,
        )
        is True
    )


def test_registry_capabilities_includes_listening_proposal():
    """
    Verify capabilities() exposes the registered capability.
    """

    executor = ListeningProposalExecutor()

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    capabilities = registry.capabilities()

    assert (
        CapabilityType.PODCAST_LISTENING_PROPOSAL
        in capabilities
    )


def test_duplicate_listening_proposal_registration_is_rejected():
    """
    Verify duplicate capability registration is rejected.
    """

    registry = CapabilityRegistry()

    registry.register(
        ListeningProposalExecutor(),
    )

    with pytest.raises(
        CapabilityAlreadyRegisteredError,
        match="already registered",
    ):
        registry.register(
            ListeningProposalExecutor(),
        )


def test_unregistered_listening_proposal_cannot_be_resolved():
    """
    Verify the registry correctly reports the capability
    when no executor has been registered.
    """

    registry = CapabilityRegistry()

    with pytest.raises(
        CapabilityNotRegisteredError,
        match="No executor registered",
    ):
        registry.resolve(
            CapabilityType.PODCAST_LISTENING_PROPOSAL,
        )


def test_registry_can_hold_listening_with_other_capabilities():
    """
    Verify Podcast Listening Proposal can coexist with
    other Runtime capabilities.
    """

    listening_executor = (
        ListeningProposalExecutor()
    )

    registry = CapabilityRegistry(
        executors=[
            listening_executor,
        ],
    )

    assert registry.contains(
        CapabilityType.PODCAST_LISTENING_PROPOSAL,
    )

    assert (
        CapabilityType.LIVE_INTELLIGENCE
        not in registry.capabilities()
    )

    assert (
        CapabilityType.PODCAST_DISCOVERY
        not in registry.capabilities()
    )

    assert (
        CapabilityType.LEARNING_GENERATION
        not in registry.capabilities()
    )