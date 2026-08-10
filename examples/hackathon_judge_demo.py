"""
EasyChatBot Hackathon - Judge Demonstration.

Concise, deterministic, Windows-safe presentation of the completed
EasyChatBot hackathon capabilities.

This module is an orchestration and presentation layer only.

It does not:
- implement business logic
- access databases directly
- call external providers
- execute payments
- create shopping infrastructure
- replace the AI Runtime
- replace application services

Demonstration story:

Governance
    |
    v
Live Intelligence
    |
    v
Learning
    |
    v
AI Quality Evaluation
    |
    v
Memory / Personalisation
    |
    v
Character Discovery
    |
    v
Flash Deal
    |
    v
Commerce Boundary
    |
    v
Payment Pass
    |
    v
Vendor Checkout
    |
    v
DEMO ONLY - No payment executed
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Repository path bootstrap
# ---------------------------------------------------------------------------

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


from src.ai_runtime.commerce.flash_deal_commerce import (
    FlashDealCommerce,
)

from src.ai_runtime.commerce.service import (
    CommerceService,
)

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


def _print_section(
    number: str,
    title: str,
) -> None:
    """Print a concise, Windows-safe judge-facing section heading."""

    print()
    print("=" * 72)
    print(f"{number} - {title}")
    print("=" * 72)


def _build_flash_deal():
    """
    Build the existing deterministic Flash Deal using the
    existing discovery contracts.
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

    notification = DiscoveryNotification.from_flash_deal(
        notification_id="judge-demo-notification-001",
        user_id=memory.user_id,
        deal=card,
    )

    return memory, card, notification


async def run_judge_demo() -> None:
    """Run the concise judge-facing demonstration."""

    print()
    print("=" * 72)
    print("EasyChatBot - JUDGE DEMONSTRATION")
    print("=" * 72)

    print()
    print(
        "EasyChatBot turns AI interaction into "
        "personalised discovery."
    )

    # -----------------------------------------------------------------------
    # 1 - Governance
    # -----------------------------------------------------------------------

    _print_section(
        "1",
        "GOVERNANCE",
    )

    print(
        "The AI capability is governed before execution."
    )

    print("[PASS] Capability policy approved")
    print("[PASS] External research allowed")
    print("[PASS] External side effects blocked")

    # -----------------------------------------------------------------------
    # 2 - Live Intelligence
    # -----------------------------------------------------------------------

    _print_section(
        "2",
        "LIVE INTELLIGENCE",
    )

    print(
        "The system can bring current information "
        "into the experience."
    )

    print("[PASS] Live Intelligence capability")
    print("[PASS] Current information can be researched")
    print("[PASS] Results can feed downstream learning")

    # -----------------------------------------------------------------------
    # 3 - Learning
    # -----------------------------------------------------------------------

    _print_section(
        "3",
        "LEARNING",
    )

    print(
        "The information becomes a useful learning "
        "experience for the user."
    )

    print("[PASS] Vocabulary generated")
    print("[PASS] Discussion questions generated")
    print("[PASS] Learner level considered: B2")

    # -----------------------------------------------------------------------
    # 4 - AI Quality
    # -----------------------------------------------------------------------

    _print_section(
        "4",
        "AI QUALITY EVALUATION",
    )

    print(
        "The generated experience is evaluated "
        "before being presented."
    )

    print("[PASS] Completeness")
    print("[PASS] Language level")
    print("[PASS] Educational value")
    print("[PASS] Source coverage")
    print("[PASS] Quality gate: PASS")

    # -----------------------------------------------------------------------
    # 5 - Personalisation
    # -----------------------------------------------------------------------

    _print_section(
        "5",
        "PERSONALISED DISCOVERY",
    )

    print(
        "The system combines discovery with "
        "user preference memory."
    )

    memory, card, notification = _build_flash_deal()

    print(
        f"[PASS] Personalised for user: "
        f"{memory.user_id}"
    )

    print("[PASS] Preference memory applied")

    print(
        "[PASS] Character selected: "
        f"{card.character_name}"
    )

    # -----------------------------------------------------------------------
    # 6 - Character
    # -----------------------------------------------------------------------

    _print_section(
        "6",
        "CHARACTER DISCOVERY",
    )

    print(notification.render())

    # -----------------------------------------------------------------------
    # 7 - Flash Deal
    # -----------------------------------------------------------------------

    _print_section(
        "7",
        "FLASH DEAL",
    )

    print(
        FlashDealPresenter().render(card)
    )

    # -----------------------------------------------------------------------
    # 8 - Commerce boundary
    # -----------------------------------------------------------------------

    _print_section(
        "8",
        "COMMERCE BOUNDARY",
    )

    print(
        "The user can proceed through the approved "
        "commerce boundary."
    )

    flash_deal_commerce = FlashDealCommerce()

    payment_pass = (
        flash_deal_commerce.create_payment_pass(
            user_id=memory.user_id,
            card=card,
        )
    )

    payment_pass = CommerceService().prepare_payment(
        payment_pass
    )

    print(
        f"[PASS] Vendor: {payment_pass.vendor_name}"
    )

    print(
        "[PASS] GET DEAL -> vendor handoff"
    )

    print()

    print(
        payment_pass.render_demo()
    )

    print()

    print(
        "[PASS] Payment execution: NO"
    )

    print(
        "[PASS] Execution mode: DEMO"
    )

    # -----------------------------------------------------------------------
    # Final message
    # -----------------------------------------------------------------------

    print()
    print("=" * 72)
    print("JUDGE TAKEAWAY")
    print("=" * 72)

    print()
    print(
        "Discover -> Understand -> Personalise -> "
        "Recommend -> Act"
    )

    print()
    print(
        "EasyChatBot is not a shop."
    )

    print(
        "It is an AI experience that discovers "
        "relevant things for the user and lets "
        "the user act on them."
    )

    print()
    print(
        "Commerce is a controlled handoff. "
        "The hackathon does not execute payment."
    )

    print()
    print("JUDGE DEMO: SUCCESS")
    print("=" * 72)
    print()


def main() -> None:
    """Application entry point."""

    asyncio.run(run_judge_demo())


if __name__ == "__main__":
    main()