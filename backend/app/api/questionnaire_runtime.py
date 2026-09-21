from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.authentication import get_current_principal
from app.application.learning_assessment.questionnaire_runtime import (
    QuestionnaireAnswerCommand,
    QuestionnaireRuntime,
)


class QuestionnaireAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)


class QuestionnaireAnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    saved: bool
    attempt_id: str
    question_id: str
    world_id: str
    correct: bool
    score: float
    reinforcement_required: bool
    reinforcement_priority: str


def create_questionnaire_runtime_router(
    *,
    runtime: QuestionnaireRuntime,
) -> APIRouter:
    if runtime is None:
        raise ValueError("runtime is required.")

    router = APIRouter(
        prefix="/api/academy/questionnaires",
        tags=["academy-questionnaires"],
    )

    @router.post(
        "/answers",
        response_model=QuestionnaireAnswerResponse,
        status_code=status.HTTP_200_OK,
    )
    async def submit_questionnaire_answer(
        payload: QuestionnaireAnswerRequest,
        principal=Depends(get_current_principal),
    ) -> QuestionnaireAnswerResponse:
        try:
            result = await runtime.submit_answer(
                command=QuestionnaireAnswerCommand(
                    learner_id=str(principal.user_id),
                    world_id=payload.world_id,
                    question_id=payload.question_id,
                    answer=payload.answer,
                )
            )
        except ValueError as exc:
            message = str(exc)

            if message == "Assessment question not found.":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=message,
                ) from exc

            if "does not belong to the requested world" in message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=message,
                ) from exc

            if message == "Answer cannot be empty.":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=message,
                ) from exc

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            ) from exc

        return QuestionnaireAnswerResponse(
            saved=True,
            attempt_id=result.attempt.attempt_id,
            question_id=result.attempt.question_id,
            world_id=result.attempt.world_id,
            correct=result.attempt.score == 1.0,
            score=float(result.attempt.score),
            reinforcement_required=(
                result.learner_skill_state.reinforcement_required
            ),
            reinforcement_priority=result.reinforcement_decision.priority.value,
        )

    return router


__all__ = [
    "QuestionnaireAnswerRequest",
    "QuestionnaireAnswerResponse",
    "create_questionnaire_runtime_router",
]
