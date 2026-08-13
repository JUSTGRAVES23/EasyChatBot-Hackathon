from decimal import Decimal

import pytest

from src.application.experience.flashcards.generator import (
    FlashCardGenerator,
)
from src.application.experience.flashcards.models import (
    CharacterPresentationContext,
    FlashCard,
)
from src.application.experience.flashcards.types import (
    FlashCardType,
)
from src.application.experience.recommendations.models import (
    ProductRecommendation,
    RecommendationAction,
)


def create_recommendation() -> ProductRecommendation:
    return ProductRecommendation(
        recommendation_id="iphone17-test",
        product_name="iPhone 17",
        description=(
            "Powerful smartphone with excellent "
            "camera and performance."
        ),
        vendor="eBay",
        vendor_url=(
            "https://example.com/iphone17"
        ),
        price=Decimal("999.99"),
        currency="EUR",
        discount_percentage=17,
        relevance_reasons=(
            "Photography",
            "Performance",
            "Discount",
        ),
        actions=(
            RecommendationAction(
                action_type="GET_DEAL",
                label="Get Deal",
                url=(
                    "https://example.com/"
                    "affiliate/iphone17"
                ),
            ),
            RecommendationAction(
                action_type="MORE_INFORMATION",
                label="More Information",
                url=(
                    "https://example.com/"
                    "iphone17"
                ),
            ),
        ),
    )


def create_character() -> CharacterPresentationContext:
    return CharacterPresentationContext(
        character_id="yeti",
        character_name="Yeti",
        opening_phrase="Look what I found! ??",
        tone="enthusiastic and curious",
    )


def test_create_product_card_returns_flashcard() -> None:
    generator = FlashCardGenerator()

    card = generator.create_product_card(
        recommendation=create_recommendation(),
        character=create_character(),
    )

    assert isinstance(card, FlashCard)


def test_product_card_uses_recommendation_id() -> None:
    card = FlashCardGenerator().create_product_card(
        recommendation=create_recommendation(),
        character=create_character(),
    )

    assert card.card_id == "iphone17-test"


def test_product_card_has_product_recommendation_type() -> None:
    card = FlashCardGenerator().create_product_card(
        recommendation=create_recommendation(),
        character=create_character(),
    )

    assert (
        card.card_type
        == FlashCardType.PRODUCT_RECOMMENDATION
    )


def test_character_personality_is_applied_to_title() -> None:
    character = create_character()

    card = FlashCardGenerator().create_product_card(
        recommendation=create_recommendation(),
        character=character,
    )

    assert card.title == "Look what I found! ??"
    assert card.character == character


def test_product_name_is_used_as_subtitle() -> None:
    card = FlashCardGenerator().create_product_card(
        recommendation=create_recommendation(),
        character=create_character(),
    )

    assert card.subtitle == "iPhone 17"


def test_relevance_reasons_become_highlights() -> None:
    card = FlashCardGenerator().create_product_card(
        recommendation=create_recommendation(),
        character=create_character(),
    )

    assert card.highlights == (
        "Photography",
        "Performance",
        "Discount",
    )


def test_product_actions_are_preserved() -> None:
    card = FlashCardGenerator().create_product_card(
        recommendation=create_recommendation(),
        character=create_character(),
    )

    assert card.actions == (
        {
            "type": "GET_DEAL",
            "label": "Get Deal",
            "url": (
                "https://example.com/"
                "affiliate/iphone17"
            ),
        },
        {
            "type": "MORE_INFORMATION",
            "label": "More Information",
            "url": (
                "https://example.com/"
                "iphone17"
            ),
        },
    )


def test_get_deal_action_is_present() -> None:
    card = FlashCardGenerator().create_product_card(
        recommendation=create_recommendation(),
        character=create_character(),
    )

    assert any(
        action["type"] == "GET_DEAL"
        for action in card.actions
    )


def test_more_information_action_is_present() -> None:
    card = FlashCardGenerator().create_product_card(
        recommendation=create_recommendation(),
        character=create_character(),
    )

    assert any(
        action["type"] == "MORE_INFORMATION"
        for action in card.actions
    )


def test_action_urls_are_preserved() -> None:
    card = FlashCardGenerator().create_product_card(
        recommendation=create_recommendation(),
        character=create_character(),
    )

    urls = {
        action["type"]: action["url"]
        for action in card.actions
    }

    assert urls["GET_DEAL"] == (
        "https://example.com/"
        "affiliate/iphone17"
    )

    assert urls["MORE_INFORMATION"] == (
        "https://example.com/"
        "iphone17"
    )


def test_generator_does_not_change_character_tone() -> None:
    character = create_character()

    card = FlashCardGenerator().create_product_card(
        recommendation=create_recommendation(),
        character=character,
    )

    assert card.character.tone == (
        "enthusiastic and curious"
    )
