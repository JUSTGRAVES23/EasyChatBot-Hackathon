from pathlib import Path

import pytest

from src.ai_agents.internal_documentation_agent.filesystem_knowledge_provider import (
    FilesystemKnowledgeProvider,
)


def test_provider_rejects_missing_root(tmp_path: Path):
    with pytest.raises(ValueError):
        FilesystemKnowledgeProvider([tmp_path / "missing"])


def test_provider_rejects_empty_query(tmp_path: Path):
    provider = FilesystemKnowledgeProvider([tmp_path])

    with pytest.raises(ValueError):
        provider.search("")


def test_provider_rejects_invalid_max_results(tmp_path: Path):
    provider = FilesystemKnowledgeProvider([tmp_path])

    with pytest.raises(ValueError):
        provider.search("Runtime", max_results=0)


def test_provider_does_not_escape_configured_root(
    tmp_path: Path,
):
    root = tmp_path / "docs"
    root.mkdir()

    outside = tmp_path / "outside.md"
    outside.write_text(
        "SECRET Runtime documentation",
        encoding="utf-8",
    )

    provider = FilesystemKnowledgeProvider([root])

    results = provider.search("SECRET Runtime")

    assert results == []
