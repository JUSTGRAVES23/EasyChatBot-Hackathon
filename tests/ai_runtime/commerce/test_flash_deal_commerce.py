"""
Tests for the Flash Deal commerce boundary.
"""

import pytest

from src.ai_runtime.commerce.flash_deal_commerce import (
    FlashDealCommerce,
)

from src.ai_runtime.commerce.models import (
    CommerceActionType,
)

from src.ai_runtime.discovery.flash_deal_demo import (
    build_demo_flash_deal_card,
)


def test_flash_deal_creates_purchase_action():

    card = build_demo_flash_deal_card()

    action = FlashDealCommerce().create_action(
        user_id="demo-user",
        card=card,
    )

    assert action.user_id == "demo-user"

    assert action.deal_id == card.deal_id

    assert (
        action.action_type
        == CommerceActionType.INITIATE_PURCHASE
    )

    assert (
        action.destination_url
        == card.get_deal_url
    )


def test_flash_deal_commerce_preserves_character_context():

    card = build_demo_flash_deal_card()

    action = FlashDealCommerce().create_action(
        user_id="demo-user",
        card=card,
    )

    assert (
        action.metadata["character_id"]
        == "yeti"
    )

    assert (
        action.metadata["vendor"]
        == card.vendor_name
    )


def test_flash_deal_commerce_rejects_empty_user():

    card = build_demo_flash_deal_card()

    with pytest.raises(
        ValueError,
        match="user_id cannot be empty",
    ):
        FlashDealCommerce().create_action(
            user_id="",
            card=card,
        )