from __future__ import annotations
from abc import ABC, abstractmethod
from .discovery_models import ProjectDiscoveryCandidate

class ProjectDiscoveryRepository(ABC):
    @abstractmethod
    def get(self, candidate_id: str) -> ProjectDiscoveryCandidate | None: ...
    @abstractmethod
    def list_candidates(self) -> list[ProjectDiscoveryCandidate]: ...
    @abstractmethod
    def find_by_key(self, candidate_key: str) -> ProjectDiscoveryCandidate | None: ...
    @abstractmethod
    def save(self, candidate: ProjectDiscoveryCandidate) -> ProjectDiscoveryCandidate: ...

__all__ = ["ProjectDiscoveryRepository"]
