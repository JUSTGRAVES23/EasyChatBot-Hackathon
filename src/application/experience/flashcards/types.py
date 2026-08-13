from __future__ import annotations

from enum import StrEnum


class FlashCardType(StrEnum):
    """
    Supported user experience cards.

    Cards are presentation contracts.

    They do not contain business logic.
    """

    PRODUCT_RECOMMENDATION = (
        "product_recommendation"
    )

    CONTENT_RECOMMENDATION = (
        "content_recommendation"
    )

    PODCAST_RECOMMENDATION = (
        "podcast_recommendation"
    )

    LEARNING_CHALLENGE = (
        "learning_challenge"
    )

    NEWS_ALERT = (
        "news_alert"
    )