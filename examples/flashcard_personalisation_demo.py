"""
EasyChatBot Hackathon Demo.

Flashcard Personalisation Demo.

Demonstrates:

Learner Memory
        |
        v
Learning Service
        |
        v
AI Runtime Capability Gateway
        |
        v
Flashcard Generation
        |
        v
Personalised Learning Content


This demo:

- uses deterministic Runtime components;
- does not call external providers;
- does not require API keys;
- does not modify production data.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


# ==========================================================
# Repository bootstrap
# ==========================================================
#
# Allows the demo to be executed directly:
#
#     python .\examples\flashcard_personalisation_demo.py
#
# without requiring external PYTHONPATH configuration.
#
# ==========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from memory.memory_service import (
    MemoryService,
)

from services.learning_service import (
    LearningService,
)

from src.ai_runtime.capabilities.flashcard_generation_executor import (
    FlashcardGenerationExecutor,
)

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)


class DemoGovernance:
    """
    Simple demo governance policy.

    Real governance remains external.
    """

    class Decision:
        allowed = True

    def evaluate(
        self,
        request,
    ):
        return self.Decision()


def build_learning_service() -> LearningService:
    """
    Create demo learning service.

    Composition only.
    """

    registry = CapabilityRegistry(
        executors=[
            FlashcardGenerationExecutor(),
        ],
    )

    gateway = CapabilityGateway(
        registry=registry,
        governance=DemoGovernance(),
    )

    return LearningService(
        capability_gateway=gateway,
    )


def print_header(
    title: str,
) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


async def main() -> None:
    """
    Execute flashcard personalisation demo.
    """

    print_header(
        "EasyChatBot - Personalised Flashcard Demo"
    )

    memory_service = MemoryService(
        database_path=(
            Path("data")
            / "demo_memory.db"
        ),
    )

    learner_id = "demo-learner-001"

    print(
        "\n1. Creating learner memory..."
    )

    memory_service.remember(
        user_id=learner_id,
        category="learning_goal",
        content=(
            "Learner is preparing B2 French "
            "and wants to improve vocabulary."
        ),
    )

    memories = memory_service.recall(
        learner_id,
    )

    learner_context = "\n".join(
        memory.content
        for memory in memories
    )

    print(
        "\nLearner Memory:"
    )

    print(
        learner_context
    )

    print(
        "\n2. Calling AI Runtime Flashcard Capability..."
    )

    learning_service = build_learning_service()

    result = await learning_service.generate_flashcards(
        request_id=(
            "demo-flashcards-001"
        ),
        topic=(
            "French vocabulary"
        ),
        learner_context=learner_context,
    )

    print_header(
        "Generated Flashcards"
    )

    flashcard_set = result.output

    for index, card in enumerate(
        flashcard_set.cards,
        start=1,
    ):
        print(
            f"\nCard {index}"
        )

        print(
            f"Front: {card.front}"
        )

        print(
            f"Back: {card.back}"
        )

        print(
            f"Example: {card.example}"
        )

    print_header(
        "Demo Completed Successfully"
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )
