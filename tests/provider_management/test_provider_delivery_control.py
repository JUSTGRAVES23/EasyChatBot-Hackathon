"""
Provider Delivery Control tests.

Validates the manual provider-management kill switch.

Tests:
- initial active state;
- manual pause;
- execution blocking;
- pause reason;
- resume;
- repeated pause/resume operations.
"""

from __future__ import annotations


import pytest


from provider_management.control.provider_delivery_control import (
    ProviderDeliveryControl,
)



def test_provider_control_starts_active() -> None:
    """
    Provider execution is allowed by default.
    """

    control = ProviderDeliveryControl()


    assert (
        control.is_paused()
        is False
    )


    assert (
        control.allow_execution()
        is True
    )


    status = (
        control.status()
    )


    assert (
        status["paused"]
        is False
    )


    assert (
        status["reason"]
        is None
    )


    assert (
        status["changed_at"]
        is None
    )



def test_provider_control_pause_blocks_execution() -> None:
    """
    Manual pause must immediately block provider execution.
    """

    control = ProviderDeliveryControl()


    control.pause(
        reason=(
            "External provider security incident"
        ),
    )


    assert (
        control.is_paused()
        is True
    )


    assert (
        control.allow_execution()
        is False
    )


    status = (
        control.status()
    )


    assert (
        status["paused"]
        is True
    )


    assert (
        status["reason"]
        == "External provider security incident"
    )


    assert (
        status["changed_at"]
        is not None
    )



def test_provider_control_resume_allows_execution() -> None:
    """
    Resume must restore provider execution.
    """

    control = ProviderDeliveryControl()


    control.pause(
        reason="Emergency provider stop",
    )


    assert (
        control.allow_execution()
        is False
    )


    control.resume()


    assert (
        control.is_paused()
        is False
    )


    assert (
        control.allow_execution()
        is True
    )


    status = (
        control.status()
    )


    assert (
        status["paused"]
        is False
    )


    assert (
        status["reason"]
        is None
    )


    assert (
        status["changed_at"]
        is not None
    )



def test_provider_control_requires_pause_reason() -> None:
    """
    A manual emergency stop must contain an operational reason.
    """

    control = ProviderDeliveryControl()


    with pytest.raises(
        ValueError,
        match="pause reason is required",
    ):

        control.pause("")



def test_provider_control_rejects_whitespace_pause_reason() -> None:
    """
    Whitespace-only reasons are invalid.
    """

    control = ProviderDeliveryControl()


    with pytest.raises(
        ValueError,
        match="pause reason is required",
    ):

        control.pause("   ")



def test_provider_control_strips_pause_reason() -> None:
    """
    Stored operational reason should be normalised.
    """

    control = ProviderDeliveryControl()


    control.pause(
        reason="  Provider incident  ",
    )


    status = (
        control.status()
    )


    assert (
        status["reason"]
        == "Provider incident"
    )


def test_provider_control_supports_repeated_operations() -> None:
    """
    The control can be stopped and resumed repeatedly.
    """

    control = ProviderDeliveryControl()


    control.pause(
        reason="First provider incident",
    )


    assert (
        control.allow_execution()
        is False
    )


    control.resume()


    assert (
        control.allow_execution()
        is True
    )


    control.pause(
        reason="Second provider incident",
    )


    assert (
        control.allow_execution()
        is False
    )


    status = (
        control.status()
    )


    assert (
        status["reason"]
        == "Second provider incident"
    )


def test_provider_control_resume_is_idempotent() -> None:
    """
    Calling resume while already active is safe.
    """

    control = ProviderDeliveryControl()


    control.resume()


    assert (
        control.is_paused()
        is False
    )


    assert (
        control.allow_execution()
        is True
    )