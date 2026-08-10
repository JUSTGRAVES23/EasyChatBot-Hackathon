"""
Integration test for:

DealCard
    ↓
CommerceAction
    ↓
CommerceService
"""

from src.ai_runtime.commerce.models import (
    CommerceAction,
    CommerceActionStatus,
    CommerceActionType,
)

from src.ai_runtime.commerce.service import (
    CommerceService,
)

from src.ai_runtime.discovery.models import (
    CommerceLink,
    DealCard,
)


def test_deal_can_become_commerce_action():

    link = CommerceLink(
        vendor="Example Vendor",
        destination_url=(
            "https://example.com/product/001"
        ),
    )

    deal = DealCard(
        product_name="Travel Backpack",
        vendor="Example Vendor",
        price=89.0,
        currency="EUR",
        commerce_link=link,
    )

    action = CommerceAction(
        user_id="user-001",
        deal_id=deal.deal_id,
        action_type=(
            CommerceActionType.INITIATE_PURCHASE
        ),
        destination_url=(
            deal.commerce_link.click_url
        ),
    )

    result = CommerceService().initiate(
        action
    )

    assert (
        result.status
        == CommerceActionStatus.REDIRECT
    )

    assert (
        result.deal_id
        == deal.deal_id
    )

    assert (
        result.next_url
        == deal.commerce_link.click_url
    )