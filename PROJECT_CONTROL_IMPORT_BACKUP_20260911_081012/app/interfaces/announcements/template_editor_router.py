from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.application.announcements.template_editor_service import (
    AnnouncementTemplateEditorService,
)


class PreviewRequest(BaseModel):
    template_id: str
    template_version: int | None = None
    values: dict[str, str] = Field(default_factory=dict)


class CreateDraftRequest(BaseModel):
    publication_id: str | None = None
    template_id: str
    template_version: int | None = None
    title: str
    values: dict[str, str] = Field(default_factory=dict)


def create_template_editor_router(
    service: AnnouncementTemplateEditorService,
) -> APIRouter:
    """Create the HTTP adapter for the template-driven editor.

    Composition owns the service. This router never creates repositories,
    providers, Telegram clients, or publication executors.
    """

    if service is None:
        raise ValueError("service cannot be None.")

    router = APIRouter(
        prefix="/api/announcement-operations/template-editor",
        tags=["announcement-operations"],
    )

    @router.get("/templates")
    def list_templates() -> list[dict[str, Any]]:
        return [asdict(item) for item in service.list_approved_templates()]

    @router.post("/preview")
    def preview(request: PreviewRequest) -> dict[str, Any]:
        try:
            result = service.preview(
                template_id=request.template_id,
                values=request.values,
                version=request.template_version,
            )
        except (LookupError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return asdict(result)

    @router.post("/drafts")
    def create_draft(request: CreateDraftRequest) -> dict[str, Any]:
        try:
            publication = service.create_draft(
                publication_id=request.publication_id or str(uuid4()),
                template_id=request.template_id,
                title=request.title,
                values=request.values,
                version=request.template_version,
            )
        except (LookupError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "id": publication.publication_id,
            "title": publication.title,
            "content": publication.content,
            "template_id": publication.template_id,
            "template_version": publication.template_version,
            "publication_type": publication.publication_type.value,
            "status": publication.status.value,
            "created_at": publication.created_at.isoformat()
            if publication.created_at
            else None,
        }

    return router

