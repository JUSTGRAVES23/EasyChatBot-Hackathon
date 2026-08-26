from __future__ import annotations

from backend.app.application.announcements.repositories import (
    AnnouncementTemplateRepository,
    PublicationRepository,
)
from backend.app.domain.announcements.publication import Publication
from backend.app.domain.announcements.template_models import AnnouncementTemplate


class InMemoryAnnouncementTemplateRepository(AnnouncementTemplateRepository):
    def __init__(self) -> None:
        self._items: dict[str, AnnouncementTemplate] = {}

    def save(self, template: AnnouncementTemplate) -> None:
        self._items[template.template_id] = template

    def get(self, template_id: str) -> AnnouncementTemplate | None:
        return self._items.get(template_id)

    def list_all(self) -> tuple[AnnouncementTemplate, ...]:
        return tuple(self._items.values())


class InMemoryPublicationRepository(PublicationRepository):
    def __init__(self) -> None:
        self._items: dict[str, Publication] = {}

    def save(self, publication: Publication) -> None:
        self._items[publication.publication_id] = publication

    def get(self, publication_id: str) -> Publication | None:
        return self._items.get(publication_id)

    def list_all(self) -> tuple[Publication, ...]:
        return tuple(self._items.values())
