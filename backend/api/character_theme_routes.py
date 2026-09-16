"""
EasyChatBot Character Theme API Routes.

Dedicated HTTP boundary for the Character Theme System.

This router is intentionally separate from api.routes
and the Character Catalogue API.

Responsibilities:

- receive character/world/language context;
- resolve the corresponding visual theme;
- return the resolved theme to the frontend.

This router does NOT:

- manage learner character selection;
- store learner state;
- execute agents;
- execute capabilities;
- create providers.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi import HTTPException

from api.character_theme import CharacterThemeService


router = APIRouter(
    prefix="/character-theme",
    tags=["character-theme"],
)


# =========================================================
# Character Theme Service
# =========================================================

# The API package lives under:
#
#     backend/api/
#
# Therefore parents[1] resolves to:
#
#     backend/
#
# The active theme configuration is owned by the backend:
#
#     backend/app/configuration/character_themes/themes/
#
# Do not resolve this from the repository-root app/ directory.
_theme_directory = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "configuration"
    / "character_themes"
    / "themes"
)


character_theme_service = CharacterThemeService(
    themes_directory=_theme_directory,
)


# =========================================================
# Character Theme Endpoint
# =========================================================


@router.get("")
def get_character_theme(
    character_id: str,
    world_id: str,
    primary_language: str,
    secondary_language: str | None = None,
):
    """
    Resolve the visual theme for a character/world/language
    context.

    This endpoint does not store learner state.

    It only resolves presentation from the supplied context.
    """

    if not character_id.strip():
        raise HTTPException(
            status_code=400,
            detail="character_id is required",
        )

    if not world_id.strip():
        raise HTTPException(
            status_code=400,
            detail="world_id is required",
        )

    if not primary_language.strip():
        raise HTTPException(
            status_code=400,
            detail="primary_language is required",
        )

    try:
        return character_theme_service.resolve(
            character_id=character_id,
            world_id=world_id,
            primary_language=primary_language,
            secondary_language=secondary_language,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to resolve character theme.",
        ) from exc