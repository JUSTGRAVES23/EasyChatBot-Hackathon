from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class InternalDocumentationRequest:
    query: str
    max_results: int = 5

    def __post_init__(self) -> None:
        query = self.query.strip()
        if not query:
            raise ValueError("query must not be empty")
        if self.max_results < 1:
            raise ValueError("max_results must be >= 1")
        if self.max_results > 50:
            raise ValueError("max_results must be <= 50")
        object.__setattr__(self, "query", query)


@dataclass(frozen=True, slots=True)
class KnowledgeResult:
    source_id: str
    title: str
    content: str
    location: str | None = None
    relevance: float | None = None


@dataclass(frozen=True, slots=True)
class InternalDocumentationResponse:
    results: Sequence[KnowledgeResult]
    result_count: int
