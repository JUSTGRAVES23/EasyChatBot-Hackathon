from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .models import KnowledgeResult


class FilesystemKnowledgeProvider:
    """Read-only filesystem-backed implementation of KnowledgeProvider.

    Only explicitly configured documentation roots are searched.
    Candidate files must resolve inside one of those roots before
    they are read.

    No files are modified and no external services are contacted.
    """

    _SUPPORTED_SUFFIXES = {
        ".md",
        ".markdown",
        ".txt",
    }

    def __init__(
        self,
        roots: Sequence[str | Path],
    ) -> None:
        if not roots:
            raise ValueError(
                "At least one documentation root is required."
            )

        resolved_roots: list[Path] = []

        for root in roots:
            path = Path(root).expanduser().resolve()

            if not path.exists():
                raise ValueError(
                    f"Documentation root does not exist: {path}"
                )

            if not path.is_dir():
                raise ValueError(
                    f"Documentation root is not a directory: {path}"
                )

            resolved_roots.append(path)

        self._roots = tuple(resolved_roots)

    def _is_within_configured_root(
        self,
        path: Path,
    ) -> bool:
        """Return True only when path is inside a configured root."""

        try:
            resolved_path = path.resolve()
        except OSError:
            return False

        for root in self._roots:
            try:
                resolved_path.relative_to(root)
            except ValueError:
                continue
            else:
                return True

        return False

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> Sequence[KnowledgeResult]:
        if not isinstance(query, str):
            raise ValueError(
                "query must be a string"
            )

        if not query.strip():
            raise ValueError(
                "query cannot be empty"
            )

        if not isinstance(max_results, int):
            raise ValueError(
                "max_results must be an integer"
            )

        if max_results < 1:
            raise ValueError(
                "max_results must be greater than zero"
            )

        terms = tuple(
            term.lower()
            for term in query.split()
            if term.strip()
        )

        matches: list[tuple[int, Path, str]] = []

        for root in self._roots:
            for path in root.rglob("*"):
                if (
                    not path.is_file()
                    or path.suffix.lower()
                    not in self._SUPPORTED_SUFFIXES
                ):
                    continue

                if not self._is_within_configured_root(path):
                    continue

                try:
                    content = path.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )
                except OSError:
                    continue

                searchable = (
                    f"{path.name}\n{content}"
                ).lower()

                score = sum(
                    searchable.count(term)
                    for term in terms
                )

                if score > 0:
                    matches.append(
                        (
                            score,
                            path,
                            content,
                        )
                    )

        matches.sort(
            key=lambda item: (
                -item[0],
                str(item[1]).lower(),
            )
        )

        results: list[KnowledgeResult] = []

        for score, path, content in matches[:max_results]:
            results.append(
                KnowledgeResult(
                    source_id=str(path),
                    title=path.stem,
                    content=content,
                    location=str(path),
                    relevance=float(score),
                )
            )

        return results
