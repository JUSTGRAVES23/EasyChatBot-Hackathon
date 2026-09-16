from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.application.announcements.repositories import PublicationRepository
from app.application.announcements.template_registry import AnnouncementTemplateRegistry
from app.domain.announcements.publication import Publication
from app.domain.announcements.template_models import PublicationStatus


@dataclass(frozen=True)
class PublicationPreview:
    publication_type: str
    template_id: str
    template_version: int
    content: str


class AnnouncementPublicationService:
    def __init__(
        self,
        *,
        templates: AnnouncementTemplateRegistry,
        publications: PublicationRepository,
    ) -> None:
        if templates is None or publications is None:
            raise ValueError("templates and publications are required.")
        self._templates = templates
        self._publications = publications

    def preview(
        self,
        *,
        template_id: str,
        values: Mapping[str, str],
        version: int | None = None,
    ) -> PublicationPreview:
        template = self._templates.get_version(template_id, version)
        content = self._templates.preview(
            template_id=template_id,
            values=dict(values),
            version=template.version,
        )
        return PublicationPreview(
            publication_type=template.publication_type.value,
            template_id=template.template_id,
            template_version=template.version,
            content=content,
        )

    def create(
        self,
        *,
        publication_id: str,
        template_id: str,
        title: str,
        values: Mapping[str, str],
        version: int | None = None,
    ) -> Publication:
        template = self._templates.get_version(template_id, version)
        content = self._templates.preview(
            template_id=template_id,
            values=dict(values),
            version=template.version,
        )
        publication = Publication(
            publication_id=publication_id,
            template_id=template.template_id,
            template_version=template.version,
            publication_type=template.publication_type,
            title=title,
            content=content,
            status=PublicationStatus.DRAFT,
        )
        self._publications.save(publication)
        return publication

    def _get(self, publication_id: str) -> Publication:
        publication = self._publications.get(publication_id)
        if publication is None:
            raise LookupError(f"Unknown publication '{publication_id}'.")
        return publication

    def request_approval(self, publication_id: str) -> Publication:
        publication = self._get(publication_id)
        publication.request_approval()
        self._publications.save(publication)
        return publication

    def approve(self, publication_id: str) -> Publication:
        publication = self._get(publication_id)
        publication.approve()
        self._publications.save(publication)
        return publication

    def begin_publish(self, publication_id: str) -> Publication:
        publication = self._get(publication_id)
        publication.begin_publish()
        self._publications.save(publication)
        return publication

    def mark_publish_failure(self, publication_id: str, reason: str) -> Publication:
        publication = self._get(publication_id)
        publication.mark_failure(reason)
        self._publications.save(publication)
        return publication

    def mark_publish_success(self, publication_id: str) -> Publication:
        publication = self._get(publication_id)
        publication.publish_success()
        self._publications.save(publication)
        return publication

