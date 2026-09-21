from __future__ import annotations

from app.application.announcements.repositories import AnnouncementTemplateRepository
from app.domain.announcements.template_models import (
    AnnouncementTemplate,
    AnnouncementTemplateVersion,
    render_template,
)


class AnnouncementTemplateRegistry:
    def __init__(self, repository: AnnouncementTemplateRepository) -> None:
        if repository is None:
            raise ValueError("repository cannot be None.")
        self._repository = repository

    def register(self, template: AnnouncementTemplate) -> None:
        if self._repository.get(template.template_id) is not None:
            raise ValueError(f"Template '{template.template_id}' already exists.")
        self._repository.save(template)

    def list_templates(self) -> tuple[AnnouncementTemplate, ...]:
        """Return the approved template catalog in deterministic order."""
        return tuple(
            sorted(
                self._repository.list_all(),
                key=lambda item: (item.name.lower(), item.template_id),
            )
        )

    def get_version(
        self,
        template_id: str,
        version: int | None = None,
    ) -> AnnouncementTemplateVersion:
        template = self._repository.get(template_id)
        if template is None:
            raise LookupError(f"Unknown template '{template_id}'.")
        return template.get_version(version)

    def preview(
        self,
        *,
        template_id: str,
        values: dict[str, str],
        version: int | None = None,
    ) -> str:
        return render_template(self.get_version(template_id, version), values)

