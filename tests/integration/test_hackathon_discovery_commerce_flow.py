"""
End-to-end integration test for the hackathon discovery journey.

Flow:

User Memory
    ↓
Deal Discovery
    ↓
Personalisation
    ↓
Character FlashDealCard
    ↓
GET DEAL
    ↓
CommerceAction
    ↓
CommerceService
    ↓
Vendor handoff

The test validates the complete hackathon vertical slice
without executing a real purchase or external payment.
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
    build_demo_deal,
    build_demo_flash_deal_card,
    build_demo_memory,
)


def test_hackathon_discovery_to_commerce_flow():
    """
    Validate the complete personalised discovery journey.
    """

    # ------------------------------------------------------------------
    # 1. USER MEMORY
    # ------------------------------------------------------------------

    memory = build_demo_memory()

    assert memory.user_id == "demo-user"

    assert memory.content

    # ------------------------------------------------------------------
    # 2. DEAL DISCOVERY
    # ------------------------------------------------------------------

    deal = build_demo_deal()

    assert deal.deal_id

    assert deal.product_name == "iPhone 17 Pro"

    assert deal.vendor == "Demo Vendor"

    assert deal.price == 999.99

    # ------------------------------------------------------------------
    # 3. PERSONALISED FLASH DEAL
    # ------------------------------------------------------------------

    card = build_demo_flash_deal_card(
        deal=deal,
    )

    assert card.deal_id == deal.deal_id

    assert card.character_id == "yeti"

    assert card.character_name == "Yeti"

    assert card.product_name == deal.product_name

    assert card.relevance_reason

    assert (
        "mobile photography"
        in card.relevance_reason
    )

    assert card.has_discount is True

    # ------------------------------------------------------------------
    # 4. COMMERCE ACTION
    # ------------------------------------------------------------------

    action = FlashDealCommerce().create_action(
        user_id=memory.user_id,
        card=card,
    )

    assert action.user_id == memory.user_id

    assert action.deal_id == card.deal_id

    assert (
        action.action_type
        == CommerceActionType.INITIATE_PURCHASE
    )

    assert (
        action.destination_url
        == card.get_deal_url
    )

    # ------------------------------------------------------------------
    # 5. CONTROLLED COMMERCE SERVICE
    # ------------------------------------------------------------------

    result = CommerceService().initiate(
        action
    )

    assert (
        result.status
        == CommerceActionStatus.REDIRECT
    )

    assert result.action_id == action.action_id

    assert result.deal_id == card.deal_id

    assert (
        result.next_url
        == card.get_deal_url
    )

    # ------------------------------------------------------------------
    # 6. FINAL SAFETY BOUNDARY
    # ------------------------------------------------------------------

    # The hackathon demonstrates a vendor handoff.
    # It does not claim that a payment occurred.

    assert (
        result.message
        == (
            "Continue to the approved vendor "
            "to complete the purchase."
        )
    )


def test_hackathon_flow_preserves_layer_separation():
    """
    Verify that commerce consumes the discovery result rather
    than changing it.
    """

    card = build_demo_flash_deal_card()

    original = {
        "deal_id": card.deal_id,
        "product_name": card.product_name,
        "price": card.current_price,
        "vendor": card.vendor_name,
        "relevance": card.relevance_reason,
        "get_deal_url": card.get_deal_url,
    }

    action = FlashDealCommerce().create_action(
        user_id="demo-user",
        card=card,
    )

    CommerceService().initiate(
        action
    )

    assert card.deal_id == original["deal_id"]

    assert (
        card.product_name
        == original["product_name"]
    )

    assert (
        card.current_price
        == original["price"]
    )

    assert (
        card.vendor_name
        == original["vendor"]
    )

    assert (
        card.relevance_reason
        == original["relevance"]
    )

    assert (
        card.get_deal_url
        == original["get_deal_url"]
    )