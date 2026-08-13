from decimal import Decimal

from src.application.experience.flashcards.generator import (
    FlashCardGenerator,
)

from src.application.experience.flashcards.models import (
    CharacterPresentationContext,
)

from src.application.experience.recommendations.models import (
    ProductRecommendation,
    RecommendationAction,
)


recommendation = ProductRecommendation(
    recommendation_id="iphone17-demo",

    product_name="iPhone 17",

    description=(
        "Powerful smartphone with excellent "
        "camera and performance."
    ),

    vendor="eBay",

    vendor_url=(
        "https://example.com/iphone17"
    ),

    price=Decimal(
        "999.99"
    ),

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


yeti = CharacterPresentationContext(
    character_id="yeti",

    character_name="Yeti",

    opening_phrase=(
        "Look what I found! 🧊"
    ),

    tone=(
        "enthusiastic and curious"
    ),

    image_url=(
        "/characters/yeti.png"
    ),
)


card = FlashCardGenerator().create_product_card(
    recommendation=recommendation,
    character=yeti,
)


print(card)