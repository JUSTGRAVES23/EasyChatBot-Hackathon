"""
Hackathon personalised Flash Idea builder.

Combines:
- a discovered DealCard
- user memory
- character identity

into a character-led discovery message.

This module does not:
- process payments
- call vendors
- call external APIs
- write memory
- execute agents
"""

from __future__ import annotations

from src.ai_runtime.discovery.models import (
    DealCard,
    FlashIdea,
)

from src.ai_runtime.memory.models import (
    MemoryEntry,
    MemoryType,
)


class FlashIdeaBuilder:
    """
    Builds a personalised FlashIdea from a deal
    and explicit user memories.
    """

    def build(
        self,
        *,
        character_id: str,
        deal: DealCard,
        memories: list[MemoryEntry],
    ) -> FlashIdea:
        """
        Build a personalised flash idea.

        Preference memories are used to explain why
        the discovery may be relevant to the user.
        """

        preferences = [
            memory
            for memory in memories
            if memory.memory_type
            == MemoryType.PREFERENCE
        ]

        if preferences:
            preference = preferences[0].content

            message = (
                f"I remembered that {preference.lower()} "
                f"I found this {deal.product_name} "
                f"at {deal.price:.2f} {deal.currency} "
                f"from {deal.vendor}."
            )
        else:
            message = (
                f"I found something you might like: "
                f"{deal.product_name} "
                f"at {deal.price:.2f} {deal.currency} "
                f"from {deal.vendor}."
            )

        if deal.discount_percentage is not None:
            message += (
                f" It's currently "
                f"{deal.discount_percentage:.0f}% off."
            )

        return FlashIdea(
            character_id=character_id,
            deal_id=deal.deal_id,
            title="Flash idea",
            message=message,
            metadata={
                "vendor": deal.vendor,
                "commerce_url": (
                    deal.commerce_link.click_url
                ),
            },
        )