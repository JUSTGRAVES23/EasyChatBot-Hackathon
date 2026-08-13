from __future__ import annotations

from src.application.experience.flashcards.models import (
    CharacterPresentationContext,
    FlashCard,
)

from src.application.experience.flashcards.types import (
    FlashCardType,
)

from src.application.experience.recommendations.models import (
    ProductRecommendation,
)


class FlashCardGenerator:
    """
    Converts recommendations into user-facing cards.

    The generator applies character personality.
    """

    def create_product_card(
        self,
        *,
        recommendation: ProductRecommendation,
        character: CharacterPresentationContext,
    ) -> FlashCard:

        return FlashCard(
            card_id=(
                recommendation.recommendation_id
            ),

            card_type=(
                FlashCardType.PRODUCT_RECOMMENDATION
            ),

            character=character,

            title=(
                character.opening_phrase
            ),

            subtitle=(
                recommendation.product_name
            ),

            highlights=(
                recommendation.relevance_reasons
            ),

            actions=tuple(
                {
                    "type": action.action_type,
                    "label": action.label,
                    "url": action.url or "",
                }
                for action in recommendation.actions
            ),
        )