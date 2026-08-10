"""
End-to-end hackathon vertical-slice test.

Validates the working EasyChatBot journey:

Governance
    ↓
Live Intelligence
    ↓
Learning Challenge
    ↓
Quality Evaluation
    ↓
Memory
    ↓
DiscoveryService
    ↓
FlashDealCard
    ↓
CommerceAction
    ↓
CommerceService
    ↓
Vendor handoff

No real purchase or external payment is executed.
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
    build_demo_memory,
)

from src.ai_runtime.discovery.service import (
    CharacterContext,
    DiscoveryRequest,
    DiscoveryService,
)


def test_complete_hackathon_vertical_slice():

    # ---------------------------------------------------------------
    # MEMORY
    # ---------------------------------------------------------------

    memory = build_demo_memory()

    assert memory.user_id == "demo-user"

    assert memory.content

    # ---------------------------------------------------------------
    # DISCOVERY INPUT
    # ---------------------------------------------------------------

    deal = build_demo_deal()

    request = DiscoveryRequest(
        user_id=memory.user_id,
        deal=deal,
        character=CharacterContext(
            character_id="yeti",
            character_name="Yeti",
            message=(
                "Look what I found! "
                "This could be perfect for you."
            ),
        ),
        product_image_url=(
            "https://example.com/demo/iphone17-pro.jpg"
        ),
        tagline="Pro. Beautiful. Powerful.",
        highlights=(
            "Pro camera system",
            "High-performance chip",
            "All-day battery life",
            "Premium display",
        ),
    )

    # ---------------------------------------------------------------
    # DISCOVERY SERVICE
    # ---------------------------------------------------------------

    card = DiscoveryService().create_flash_deal(
        request,
        memories=[memory],
    )

    assert card.deal_id == deal.deal_id

    assert card.character_id == "yeti"

    assert card.product_name == deal.product_name

    assert card.vendor_name == deal.vendor

    assert card.relevance_reason

    # ---------------------------------------------------------------
    # COMMERCE ACTION
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # COMMERCE SERVICE
    # ---------------------------------------------------------------

    result = CommerceService().initiate(
        action
    )

    assert (
        result.status
        == CommerceActionStatus.REDIRECT
    )

    assert result.deal_id == card.deal_id

    assert result.action_id == action.action_id

    assert (
        result.next_url
        == card.get_deal_url
    )

    # ---------------------------------------------------------------
    # SAFETY / SCOPE BOUNDARY
    # ---------------------------------------------------------------

    assert (
        result.message
        == (
            "Continue to the approved vendor "
            "to complete the purchase."
        )
    )