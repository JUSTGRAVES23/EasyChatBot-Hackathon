"""
Cybersecurity Delivery Control tests.

Validates the human governance kill switch for
cybersecurity notification delivery.

Tests:
- initial active state;
- pause;
- paused status;
- resume;
- restored active state.
"""

from __future__ import annotations


from backend.cybersecurity.control.cybersecurity_delivery_control import (
    CybersecurityDeliveryControl,
)


def test_delivery_control_starts_active() -> None:
    control = CybersecurityDeliveryControl()

    assert control.is_paused() is False

    status = control.status()

    assert status["paused"] is False
    assert status["reason"] is None


def test_delivery_control_pause_blocks_delivery() -> None:
    control = CybersecurityDeliveryControl()

    control.pause(
        reason="Security incident investigation",
    )

    assert control.is_paused() is True

    status = control.status()

    assert status["paused"] is True
    assert (
        status["reason"]
        == "Security incident investigation"
    )
    assert status["changed_at"] is not None


def test_delivery_control_resume_restores_delivery() -> None:
    control = CybersecurityDeliveryControl()

    control.pause(
        reason="Emergency stop",
    )

    assert control.is_paused() is True

    control.resume()

    assert control.is_paused() is False

    status = control.status()

    assert status["paused"] is False
    assert status["reason"] is None
    assert status["changed_at"] is not None


def test_delivery_control_can_be_paused_and_resumed_multiple_times() -> None:
    control = CybersecurityDeliveryControl()

    control.pause(
        reason="First emergency stop",
    )

    assert control.is_paused() is True

    control.resume()

    assert control.is_paused() is False

    control.pause(
        reason="Second emergency stop",
    )

    assert control.is_paused() is True

    status = control.status()

    assert status["reason"] == "Second emergency stop"
