from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.announcements.publication import Publication
from app.domain.announcements.template_models import AnnouncementTemplate


class AnnouncementTemplateRepository(ABC):
    @abstractmethod
    def save(self, template: AnnouncementTemplate) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, template_id: str) -> AnnouncementTemplate | None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> tuple[AnnouncementTemplate, ...]:
        raise NotImplementedError


class PublicationRepository(ABC):
    @abstractmethod
    def save(self, publication: Publication) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, publication_id: str) -> Publication | None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> tuple[Publication, ...]:
        raise NotImplementedError

