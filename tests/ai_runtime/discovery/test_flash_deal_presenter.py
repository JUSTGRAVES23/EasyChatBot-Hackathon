"""
Tests for the FlashDealPresenter.

The presenter must remain a pure presentation layer over
FlashDealCard.
"""

from src.ai_runtime.discovery.flash_deal_demo import (
    build_demo_flash_deal_card,
)

from src.ai_runtime.discovery.flash_deal_presenter import (
    FlashDealPresenter,
)


def test_presenter_renders_character():

    card = build_demo_flash_deal_card()

    output = FlashDealPresenter().render(card)

    assert "## Yeti" in output

    assert (
        "Look what I found!"
        in output
    )


def test_presenter_renders_product():

    card = build_demo_flash_deal_card()

    output = FlashDealPresenter().render(card)

    assert "iPhone 17 Pro" in output

    assert (
        "Pro. Beautiful. Powerful."
        in output
    )


def test_presenter_renders_highlights():

    card = build_demo_flash_deal_card()

    output = FlashDealPresenter().render(card)

    assert "### HIGHLIGHTS" in output

    for highlight in card.highlights:
        assert highlight in output


def test_presenter_renders_verified_pricing():

    card = build_demo_flash_deal_card()

    output = FlashDealPresenter().render(card)

    assert "### PRICE" in output

    assert (
        f"{card.currency} "
        f"{card.current_price:.2f}"
        in output
    )

    assert (
        f"{card.currency} "
        f"{card.previous_price:.2f}"
        in output
    )

    assert (
        card.display_discount
        in output
    )

    assert (
        card.display_savings
        in output
    )


def test_presenter_renders_personalisation():

    card = build_demo_flash_deal_card()

    output = FlashDealPresenter().render(card)

    assert (
        "### WHY THIS IS RELEVANT TO YOU"
        in output
    )

    assert (
        card.relevance_reason
        in output
    )


def test_presenter_renders_vendor():

    card = build_demo_flash_deal_card()

    output = FlashDealPresenter().render(card)

    assert "### AVAILABLE FROM" in output

    assert card.vendor_name in output


def test_presenter_renders_commerce_actions():

    card = build_demo_flash_deal_card()

    output = FlashDealPresenter().render(card)

    assert "### ACTIONS" in output

    assert (
        f"[GET DEAL]({card.get_deal_url})"
        in output
    )

    assert (
        "[MORE INFORMATION]"
        f"({card.more_information_url})"
        in output
    )


def test_presenter_does_not_mutate_card():

    card = build_demo_flash_deal_card()

    original = {
        "deal_id": card.deal_id,
        "product_name": card.product_name,
        "price": card.current_price,
        "vendor": card.vendor_name,
        "relevance": card.relevance_reason,
        "get_deal_url": card.get_deal_url,
        "more_information_url": (
            card.more_information_url
        ),
    }

    FlashDealPresenter().render(card)

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

    assert (
        card.more_information_url
        == original["more_information_url"]
    )