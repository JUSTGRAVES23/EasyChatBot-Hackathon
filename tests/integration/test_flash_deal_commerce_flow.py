"""
Integration test for the complete Flash Deal commerce flow.

Flow:

Memory / personalisation
        ↓
DealCard
        ↓
FlashDealCard
        ↓
CommerceAction
        ↓
CommerceService
        ↓
External vendor handoff

No payment is executed by the test.
"""

from src.ai_runtime.commerce.flash_deal_commerce import (
    FlashDealCommerce,
)

from src.ai_runtime.commerce.models import (
    CommerceActionStatus,
    CommerceActionType,
)

from src.ai_runtime.commerce.service import (
    CommerceService,
)

from src.ai_runtime.discovery.flash_deal_demo import (
    build_demo_flash_deal_card,
)


def test_complete_flash_deal_to_commerce_flow():
    """
    Validate the complete hackathon commerce boundary.
    """

    card = build_demo_flash_deal_card()

    commerce = FlashDealCommerce()

    action = commerce.create_action(
        user_id="demo-user",
        card=card,
    )

    assert action.user_id == "demo-user"

    assert action.deal_id == card.deal_id

    assert (
        action.action_type
        == CommerceActionType.INITIATE_PURCHASE
    )

    result = CommerceService().initiate(
        action
    )

    assert (
        result.status
        == CommerceActionStatus.REDIRECT
    )

    assert result.deal_id == card.deal_id

    assert (
        result.next_url
        == card.get_deal_url
    )

    assert result.action_id == action.action_id


def test_commerce_flow_does_not_change_discovery_data():
    """
    Commerce must not mutate the discovered Flash Deal.
    """

    card = build_demo_flash_deal_card()

    original_product = card.product_name
    original_price = card.current_price
    original_vendor = card.vendor_name
    original_deal_id = card.deal_id

    action = FlashDealCommerce().create_action(
        user_id="demo-user",
        card=card,
    )

    CommerceService().initiate(
        action
    )

    assert card.product_name == original_product
    assert card.current_price == original_price
    assert card.vendor_name == original_vendor
    assert card.deal_id == original_deal_id