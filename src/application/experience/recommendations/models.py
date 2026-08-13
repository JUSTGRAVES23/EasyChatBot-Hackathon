from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RecommendationAction:
    """
    User action available on a recommendation.
    """

    action_type: str

    label: str

    url: str | None = None


@dataclass(frozen=True, slots=True)
class ProductRecommendation:
    """
    Provider-independent product recommendation.

    This is the intelligence output.

    It does not know about UI rendering.
    """

    recommendation_id: str

    product_name: str

    description: str

    vendor: str

    vendor_url: str

    price: Decimal

    currency: str

    discount_percentage: int

    relevance_reasons: tuple[str, ...]

    actions: tuple[RecommendationAction, ...]