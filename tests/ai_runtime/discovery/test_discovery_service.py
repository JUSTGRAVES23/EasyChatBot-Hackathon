"""
Tests for the hackathon DiscoveryService.

Flow:

DealCard
    +
Memory
    +
CharacterContext
    ↓
DiscoveryService
    ↓
FlashDealCard
"""

import pytest

from src.ai_runtime.discovery.models import (
    CommerceLink,
    DealCard,
)

from src.ai_runtime.discovery.service import (
    CharacterContext,
    DiscoveryRequest,
    DiscoveryService,
)

from src.ai_runtime.memory.models import (
    MemoryEntry,
    MemoryType,
)


def make_deal() -> DealCard:
    """
    Create deterministic discovery data for tests.
    """

    return DealCard(
        product_name="iPhone 17 Pro",
        vendor="Demo Vendor",
        price=999.99,
        currency="EUR",
        previous_price=1199.00,
        discount_percentage=17.0,
        commerce_link=CommerceLink(
            vendor="Demo Vendor",
            destination_url=(
                "https://example.com/product"
            ),
        ),
        source="test",
        description="Test discovery product.",
    )


def make_request() -> DiscoveryRequest:
    """
    Create a deterministic discovery request.
    """

    return DiscoveryRequest(
        user_id="user-001",
        deal=make_deal(),
        character=CharacterContext(
            character_id="yeti",
            character_name="Yeti",
            message=(
                "Look what I found! "
                "This could be perfect for you."
            ),
        ),
        product_image_url=(
            "https://example.com/product.jpg"
        ),
        tagline="Pro. Beautiful. Powerful.",
        highlights=(
            "Pro camera system",
            "High-performance chip",
            "All-day battery life",
        ),
    )


def make_preference_memory() -> MemoryEntry:
    """
    Create explicit user preference memory.
    """

    return MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.PREFERENCE,
        content=(
            "prefer powerful mobile photography "
            "devices"
        ),
    )


def test_discovery_service_creates_flash_deal():

    request = make_request()

    result = DiscoveryService().create_flash_deal(
        request
    )

    assert result.deal_id == request.deal.deal_id

    assert result.product_name == "iPhone 17 Pro"

    assert result.vendor_name == "Demo Vendor"

    assert result.character_id == "yeti"

    assert result.character_name == "Yeti"

    assert result.current_price == 999.99

    assert result.discount_percentage == 17.0


def test_discovery_service_applies_preference_memory():

    request = make_request()

    memory = make_preference_memory()

    result = DiscoveryService().create_flash_deal(
        request,
        memories=[memory],
    )

    assert (
        "powerful mobile photography devices"
        in result.relevance_reason
    )


def test_discovery_service_does_not_require_memory():

    request = make_request()

    result = DiscoveryService().create_flash_deal(
        request,
        memories=[],
    )

    assert result.relevance_reason == (
        "This discovery may be relevant to your interests."
    )


def test_discovery_service_ignores_non_preference_memory():

    request = make_request()

    non_preference_type = next(
        memory_type
        for memory_type in MemoryType
        if memory_type != MemoryType.PREFERENCE
    )

    memory = MemoryEntry(
        user_id="user-001",
        memory_type=non_preference_type,
        content=(
            "Discussed photography during the "
            "previous conversation."
        ),
    )

    result = DiscoveryService().create_flash_deal(
        request,
        memories=[memory],
    )

    assert result.relevance_reason == (
        "This discovery may be relevant to your interests."
    )


def test_discovery_service_preserves_deal_identity():

    deal = make_deal()

    request = DiscoveryRequest(
        user_id="user-001",
        deal=deal,
        character=CharacterContext(
            character_id="yeti",
            character_name="Yeti",
            message="I found something for you.",
        ),
        product_image_url=(
            "https://example.com/product.jpg"
        ),
        tagline="A useful discovery.",
        highlights=(
            "Useful",
            "Practical",
        ),
    )

    result = DiscoveryService().create_flash_deal(
        request
    )

    assert result.deal_id == deal.deal_id


def test_discovery_service_preserves_character_context():

    request = make_request()

    result = DiscoveryService().create_flash_deal(
        request
    )

    assert result.character_id == "yeti"

    assert result.character_name == "Yeti"

    assert result.character_message == (
        "Look what I found! "
        "This could be perfect for you."
    )


def test_discovery_service_rejects_empty_user_id():

    with pytest.raises(
        ValueError,
        match="user_id cannot be empty",
    ):
        DiscoveryRequest(
            user_id="",
            deal=make_deal(),
            character=CharacterContext(
                character_id="yeti",
                character_name="Yeti",
                message="I found something.",
            ),
            product_image_url=(
                "https://example.com/product.jpg"
            ),
            tagline="A useful discovery.",
            highlights=("Useful",),
        )


def test_character_context_rejects_empty_character_id():

    with pytest.raises(
        ValueError,
        match="character_id cannot be empty",
    ):
        CharacterContext(
            character_id="",
            character_name="Yeti",
            message="I found something.",
        )


def test_discovery_request_rejects_empty_highlights():

    with pytest.raises(
        ValueError,
        match="at least one highlight",
    ):
        DiscoveryRequest(
            user_id="user-001",
            deal=make_deal(),
            character=CharacterContext(
                character_id="yeti",
                character_name="Yeti",
                message="I found something.",
            ),
            product_image_url=(
                "https://example.com/product.jpg"
            ),
            tagline="A useful discovery.",
            highlights=(),
        )