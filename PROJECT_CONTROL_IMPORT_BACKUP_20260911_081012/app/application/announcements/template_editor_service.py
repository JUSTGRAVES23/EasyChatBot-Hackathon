from __future__ import annotations

from typing import Mapping

from app.application.announcements.publication_service import (
    AnnouncementPublicationService,
)
from app.application.announcements.template_editor_models import (
    TemplateEditorOption,
    TemplateEditorPreview,
    build_editor_fields,
)
from app.application.announcements.template_registry import (
    AnnouncementTemplateRegistry,
)


class AnnouncementTemplateEditorService:
    """Application service for the template-driven publication editor.

    This service only prepares editor metadata, validates/preview-renders
    template values, and creates drafts. It has no channel/provider dependency
    and never performs external publication.
    """

    def __init__(
        self,
        *,
        templates: AnnouncementTemplateRegistry,
        publications: AnnouncementPublicationService,
    ) -> None:
        if templates is None or publications is None:
            raise ValueError("templates and publications are required.")
        self._templates = templates
        self._publications = publications

    def list_approved_templates(self) -> tuple[TemplateEditorOption, ...]:
        template_models = self._templates.list_templates()

        return tuple(
            TemplateEditorOption(
                template_id=template.template_id,
                name=template.name,
                category=(
                    template.category
                    if template.category
                    else template.publication_type.value
                ),
                description=template.description
                or "Approved announcement pattern.",
                version=template.active_version,
                publication_type=template.publication_type.value,
                fields=build_editor_fields(
                    template.get_version().required_fields,
                    template.get_version().optional_fields,
                ),
            )
            for template in template_models
        )

    def preview(
        self,
        *,
        template_id: str,
        values: Mapping[str, str],
        version: int | None = None,
    ) -> TemplateEditorPreview:
        result = self._publications.preview(
            template_id=template_id,
            values=values,
            version=version,
        )
        return TemplateEditorPreview(
            template_id=result.template_id,
            template_version=result.template_version,
            publication_type=result.publication_type,
            content=result.content,
        )

    def create_draft(
        self,
        *,
        publication_id: str,
        template_id: str,
        title: str,
        values: Mapping[str, str],
        version: int | None = None,
    ):
        return self._publications.create(
            publication_id=publication_id,
            template_id=template_id,
            title=title,
            values=values,
            version=version,
        )

