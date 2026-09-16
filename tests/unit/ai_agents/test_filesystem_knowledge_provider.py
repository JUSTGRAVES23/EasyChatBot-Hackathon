from pathlib import Path

from src.ai_agents.internal_documentation_agent.filesystem_knowledge_provider import (
    FilesystemKnowledgeProvider,
)


def test_filesystem_provider_returns_matching_documents(tmp_path: Path):
    document = tmp_path / "runtime.md"
    document.write_text(
        "# Runtime\n\nCapability execution is governed by the Runtime.",
        encoding="utf-8",
    )

    provider = FilesystemKnowledgeProvider([tmp_path])

    results = provider.search("Runtime capability")

    assert len(results) == 1
    assert results[0].title == "runtime"
    assert "Capability execution" in results[0].content
    assert results[0].location == str(document.resolve())


def test_filesystem_provider_respects_max_results(tmp_path: Path):
    for index in range(3):
        (tmp_path / f"doc-{index}.md").write_text(
            "Runtime capability",
            encoding="utf-8",
        )

    provider = FilesystemKnowledgeProvider([tmp_path])

    results = provider.search("Runtime", max_results=2)

    assert len(results) == 2


def test_filesystem_provider_ignores_unsupported_files(tmp_path: Path):
    (tmp_path / "allowed.md").write_text(
        "Runtime",
        encoding="utf-8",
    )
    (tmp_path / "ignored.py").write_text(
        "Runtime",
        encoding="utf-8",
    )

    provider = FilesystemKnowledgeProvider([tmp_path])

    results = provider.search("Runtime")

    assert len(results) == 1
    assert results[0].title == "allowed"


def test_filesystem_provider_is_read_only(tmp_path: Path):
    document = tmp_path / "runtime.md"
    document.write_text("Runtime", encoding="utf-8")

    before = document.read_text(encoding="utf-8")

    provider = FilesystemKnowledgeProvider([tmp_path])
    provider.search("Runtime")

    after = document.read_text(encoding="utf-8")

    assert after == before
