"""
Tests for the hackathon Commerce Service.
"""

import pytest

from src.ai_runtime.commerce.models import (
    CommerceAction,
    CommerceActionResult,
    CommerceActionStatus,
    CommerceActionType,
)

from src.ai_runtime.commerce.service import (
    CommerceService,
)


def make_action() -> CommerceAction:
    return CommerceAction(
        user_id="user-001",
        deal_id="deal-001",
        action_type=(
            CommerceActionType.INITIATE_PURCHASE
        ),
        destination_url=(
            "https://example.com/product/001"
        ),
    )


def test_commerce_action_is_created():

    action = make_action()

    assert action.user_id == "user-001"

    assert action.deal_id == "deal-001"

    assert (
        action.action_type
        == CommerceActionType.INITIATE_PURCHASE
    )

    assert (
        action.destination_url
        == "https://example.com/product/001"
    )

    assert action.action_id


def test_commerce_service_returns_vendor_handoff():

    action = make_action()

    result = CommerceService().initiate(
        action
    )

    assert isinstance(
        result,
        CommerceActionResult,
    )

    assert (
        result.status
        == CommerceActionStatus.REDIRECT
    )

    assert (
        result.next_url
        == action.destination_url
    )

    assert result.deal_id == action.deal_id


def test_commerce_action_rejects_empty_user():

    with pytest.raises(
        ValueError,
        match="user_id cannot be empty",
    ):
        CommerceAction(
            user_id="",
            deal_id="deal-001",
            action_type=(
                CommerceActionType.INITIATE_PURCHASE
            ),
            destination_url=(
                "https://example.com/product/001"
            ),
        )


def test_commerce_action_rejects_invalid_url():

    with pytest.raises(
        ValueError,
        match="HTTP or HTTPS",
    ):
        CommerceAction(
            user_id="user-001",
            deal_id="deal-001",
            action_type=(
                CommerceActionType.INITIATE_PURCHASE
            ),
            destination_url="invalid-url",
        )