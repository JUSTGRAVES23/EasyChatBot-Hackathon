"""
EasyChatBot API Routes.

The API layer exposes the application.

Routes do not contain agent logic.
They delegate execution to application services.
"""

from fastapi import APIRouter, HTTPException

from backend.characters.character_registry import (
    CharacterRegistry,
)

from backend.services.companion_service import (
    CompanionService,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


router = APIRouter()

character_registry = CharacterRegistry()


def create_companion_service(
    character,
) -> CompanionService:
    """
    Create the application-level CompanionService.

    Kept as a small dependency seam so API tests can
    replace the service without invoking external providers.

    Production behaviour remains the same.
    """

    return CompanionService(
        character=character
    )


@router.get("/characters")
def get_characters():
    """
    Return available AI companions.
    """

    characters = (
        character_registry.list_characters()
    )

    return {
        "characters": [
            {
                "id": character.character_id,
                "name": character.name,
                "description": character.description,
                "personality": character.personality,
                "learning_style": character.learning_style,
            }
            for character in characters
        ]
    }


@router.post("/chat")
async def chat(
    payload: dict,
):
    """
    Execute an EasyChatBot companion interaction.

    Expected payload:

    {
        "user_id": "demo-user",
        "character": "yeti",
        "message": "Explain AI",
        "research": false
    }
    """

    message = payload.get("message")

    if not message:
        raise HTTPException(
            status_code=400,
            detail="message is required",
        )

    character_id = payload.get(
        "character",
        "yeti",
    )

    try:
        character = character_registry.get(
            character_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    companion_service = (
        create_companion_service(
            character
        )
    )

    context = ExecutionContext(
        user_id=payload.get(
            "user_id",
            "demo-user",
        ),
        request=message,
    )

    result = await companion_service.interact(
        context,
        use_research=payload.get(
            "research",
            False,
        ),
    )

    return result