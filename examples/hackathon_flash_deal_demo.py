"""
EasyChatBot Hackathon — Flash Deal Experience.

Presentation-only demonstration of the personalised discovery
experience.

The production/framework flow remains:

Memory
    |
    v
DiscoveryService
    |
    v
FlashDealCard
    |
    v
FlashDealPresenter
    |
    v
Character Notification
    |
    v
Commerce boundary
"""

from __future__ import annotations

import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Repository path bootstrap
# ---------------------------------------------------------------------------

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


from src.ai_runtime.discovery.flash_deal_demo import (
    build_demo_deal,
    build_demo_memory,
)

from src.ai_runtime.discovery.flash_deal_presenter import (
    FlashDealPresenter,
)

from src.ai_runtime.discovery.notification import (
    DiscoveryNotification,
)

from src.ai_runtime.discovery.service import (
    CharacterContext,
    DiscoveryRequest,
    DiscoveryService,
)


def build_flash_deal_experience() -> str:
    """
    Build the complete user-facing Flash Deal experience.

    All business/domain data is produced through the existing
    discovery contracts.
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

    notification = (
        DiscoveryNotification.from_flash_deal(
            notification_id="flash-deal-demo-001",
            user_id=memory.user_id,
            deal=card,
        )
    )

    presenter = FlashDealPresenter()

    return "\n".join(
        [
            "",
            "=" * 72,
            "PERSONALISED DISCOVERY",
            "=" * 72,
            "",
            notification.render(),
            "",
            presenter.render(card),
            "",
            "=" * 72,
        ]
    )


def main() -> None:
    """Run the Flash Deal experience demo."""

    print(
        build_flash_deal_experience()
    )


if __name__ == "__main__":
    main()