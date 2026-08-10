"""
Integration test for the character-driven discovery notification.

Flow:

Memory
    ↓
DiscoveryService
    ↓
FlashDealCard
    ↓
DiscoveryNotification
    ↓
CommerceAction
    ↓
CommerceService
    ↓
Vendor handoff
"""

from src.ai_runtime.commerce.flash_deal_commerce import (
    FlashDealCommerce,
)

from src.ai_runtime.commerce.models import (
    CommerceActionStatus,
)

from src.ai_runtime.commerce.service import (
    CommerceService,
)

from src.ai_runtime.discovery.flash_deal_demo import (
    build_demo_deal,
    build_demo_memory,
)

from src.ai_runtime.discovery.notification import (
    DiscoveryNotification,
)

from src.ai_runtime.discovery.service import (
    CharacterContext,
    DiscoveryRequest,
    DiscoveryService,
)


def build_flash_deal():
    """
    Build the same application-level FlashDealCard used
    by the hackathon discovery flow.
    """

    deal = build_demo_deal()
    memory = build_demo_memory()

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

    card = DiscoveryService().create_flash_deal(
        request,
        memories=[memory],
    )

    return memory, card


def test_notification_is_created_from_real_discovery_result():

    memory, card = build_flash_deal()

    notification = (
        DiscoveryNotification.from_flash_deal(
            notification_id="integration-notification-001",
            user_id=memory.user_id,
            deal=card,
        )
    )

    assert notification.user_id == memory.user_id

    assert notification.character_id == (
        card.character_id
    )

    assert notification.character_name == (
        card.character_name
    )

    assert notification.deal is card

    assert notification.product_name == (
        card.product_name
    )


def test_notification_preserves_personalisation():

    memory, card = build_flash_deal()

    notification = (
        DiscoveryNotification.from_flash_deal(
            notification_id="integration-notification-002",
            user_id=memory.user_id,
            deal=card,
        )
    )

    assert notification.relevance_reason == (
        card.relevance_reason
    )

    assert notification.relevance_reason


def test_notification_render_is_character_driven():

    memory, card = build_flash_deal()

    notification = (
        DiscoveryNotification.from_flash_deal(
            notification_id="integration-notification-003",
            user_id=memory.user_id,
            deal=card,
        )
    )

    rendered = notification.render()

    assert "Yeti:" in rendered

    assert (
        "Look what I found!"
        in rendered
    )

    assert card.product_name in rendered

    assert (
        card.relevance_reason
        in rendered
    )


def test_notification_does_not_change_commerce_flow():

    memory, card = build_flash_deal()

    notification = (
        DiscoveryNotification.from_flash_deal(
            notification_id="integration-notification-004",
            user_id=memory.user_id,
            deal=card,
        )
    )

    action = FlashDealCommerce().create_action(
        user_id=notification.user_id,
        card=notification.deal,
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


def test_notification_does_not_create_a_shop():

    memory, card = build_flash_deal()

    notification = (
        DiscoveryNotification.from_flash_deal(
            notification_id="integration-notification-005",
            user_id=memory.user_id,
            deal=card,
        )
    )

    # The notification exposes one discovery event,
    # not a catalogue, cart, or shopping dashboard.

    assert notification.deal is card

    assert not hasattr(
        notification,
        "products",
    )

    assert not hasattr(
        notification,
        "cart",
    )

    assert not hasattr(
        notification,
        "checkout",
    )