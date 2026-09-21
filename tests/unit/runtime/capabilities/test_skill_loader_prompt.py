from __future__ import annotations

from pathlib import Path

import pytest

from runtime.capabilities.loaders.skill_loader import SkillLoader


def test_load_prompt_reads_resource(tmp_path: Path) -> None:
    skill_dir = tmp_path / "architecture_review"
    skill_dir.mkdir()

    (skill_dir / "prompt.md").write_text(
        "Review architecture.",
        encoding="utf-8",
    )

    loader = SkillLoader(tmp_path)

    assert (
        loader.load_prompt(
            "architecture_review",
            "prompt.md",
        )
        == "Review architecture."
    )


def test_load_prompt_rejects_path_traversal(tmp_path: Path) -> None:
    skill_dir = tmp_path / "architecture_review"
    skill_dir.mkdir()

    (tmp_path / "outside.md").write_text(
        "outside",
        encoding="utf-8",
    )

    loader = SkillLoader(tmp_path)

    with pytest.raises(ValueError, match="outside"):
        loader.load_prompt(
            "architecture_review",
            "../outside.md",
        )


def test_load_prompt_rejects_missing_resource(tmp_path: Path) -> None:
    skill_dir = tmp_path / "architecture_review"
    skill_dir.mkdir()

    loader = SkillLoader(tmp_path)

    with pytest.raises(FileNotFoundError):
        loader.load_prompt(
            "architecture_review",
            "missing.md",
        )
