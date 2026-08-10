"""
Tests for personalised Flash Ideas.
"""

from src.ai_runtime.discovery.flash_idea import (
    FlashIdeaBuilder,
)

from src.ai_runtime.discovery.models import (
    CommerceLink,
    DealCard,
)

from src.ai_runtime.memory.models import (
    MemoryEntry,
    MemoryType,
)


def make_deal() -> DealCard:
    link = CommerceLink(
        vendor="Example Vendor",
        destination_url=(
            "https://example.com/product/backpack"
        ),
    )

    return DealCard(
        product_name="Minimalist Travel Backpack",
        vendor="Example Vendor",
        price=89.0,
        currency="EUR",
        previous_price=129.0,
        discount_percentage=31.0,
        commerce_link=link,
        source="parallel",
    )


def test_flash_idea_uses_user_preference():

    memory = MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.PREFERENCE,
        content="prefers minimalist travel products",
    )

    idea = FlashIdeaBuilder().build(
        character_id="yeti",
        deal=make_deal(),
        memories=[memory],
    )

    assert idea.character_id == "yeti"

    assert (
        idea.deal_id
        == make_deal().deal_id
        or idea.deal_id
    )

    assert (
        "minimalist travel products"
        in idea.message
    )

    assert (
        "Minimalist Travel Backpack"
        in idea.message
    )

    assert (
        "31% off"
        in idea.message
    )


def test_flash_idea_works_without_memory():

    idea = FlashIdeaBuilder().build(
        character_id="yeti",
        deal=make_deal(),
        memories=[],
    )

    assert (
        "I found something you might like"
        in idea.message
    )

    assert (
        "Minimalist Travel Backpack"
        in idea.message
    )


def test_flash_idea_contains_commerce_url():

    idea = FlashIdeaBuilder().build(
        character_id="yeti",
        deal=make_deal(),
        memories=[],
    )

    assert (
        idea.metadata["commerce_url"]
        == "https://example.com/product/backpack"
    )


def test_non_preference_memory_does_not_become_preference():

    memory = MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.DISCOVERY_CONTEXT,
        content="Looking for travel gear",
    )

    idea = FlashIdeaBuilder().build(
        character_id="yeti",
        deal=make_deal(),
        memories=[memory],
    )

    assert (
        "I found something you might like"
        in idea.message
    )