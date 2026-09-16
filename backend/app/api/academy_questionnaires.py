from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/api/academy",
    tags=["academy-questionnaires"],
)


STATIC_QUESTIONNAIRES: dict[str, list[dict[str, Any]]] = {
    "french": [
        {
            "id": "french-b1-b2",
            "world_id": "french",
            "title": "French B1 → B2",
            "subtitle": "Grammar · Vocabulary · Comprehension",
            "description": (
                "A balanced challenge to strengthen the skills "
                "you need for your next level."
            ),
            "recommended": True,
            "recommendation_reason": (
                "Recommended based on your Academy activity."
            ),
        },
        {
            "id": "french-conversation",
            "world_id": "french",
            "title": "French Conversation",
            "subtitle": "Speak naturally · React · Understand",
            "description": (
                "Less textbook. More actually talking to humans."
            ),
            "recommended": False,
            "recommendation_reason": None,
        },
        {
            "id": "professional-french",
            "world_id": "french",
            "title": "Professional French",
            "subtitle": "Business · Meetings · Workplace vocabulary",
            "description": (
                "Because one day, bonjour has to become "
                "Bonjour, concernant le dossier..."
            ),
            "recommended": False,
            "recommendation_reason": None,
        },
    ],
}


@router.get("/worlds/{world_id}/questionnaires")
async def get_world_questionnaires(
    world_id: str,
) -> dict[str, Any]:
    world = world_id.strip().lower()

    questionnaires = STATIC_QUESTIONNAIRES.get(world)

    if questionnaires is None:
        raise HTTPException(
            status_code=404,
            detail=f"Academy world '{world_id}' was not found.",
        )

    recommended = next(
        (
            questionnaire
            for questionnaire in questionnaires
            if questionnaire["recommended"]
        ),
        None,
    )

    return {
        "world_id": world,
        "questionnaires": questionnaires,
        "recommended_questionnaire_id": (
            recommended["id"] if recommended else None
        ),
    }