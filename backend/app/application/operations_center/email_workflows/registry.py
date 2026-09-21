from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from .domain import EmailWorkflowDefinition


class EmailWorkflowRegistry(ABC):
    """Authoritative application boundary for email workflows."""

    @abstractmethod
    def create(
        self,
        workflow: EmailWorkflowDefinition,
    ) -> EmailWorkflowDefinition:
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        workflow_id: str,
    ) -> EmailWorkflowDefinition | None:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> Sequence[EmailWorkflowDefinition]:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        workflow: EmailWorkflowDefinition,
    ) -> EmailWorkflowDefinition:
        raise NotImplementedError
