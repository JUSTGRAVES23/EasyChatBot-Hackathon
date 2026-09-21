from __future__ import annotations

from pathlib import Path

from app.application.uai.world.world_resolver import (
    WorldResolver,
)
from app.infrastructure.worlds.yaml_world_repository import (
    YamlWorldRepository,
)


def create_world_resolver() -> WorldResolver:
    """
    Build the same real YAML-backed WorldResolver used by the
    application runtime.

    Test location:
        backend/tests/application/uai/world/

    Repository root:
        backend/
    """
    backend_root = Path(__file__).resolve().parents[4]

    worlds_path = (
        backend_root
        / "app"
        / "configuration"
        / "worlds"
    )

    return WorldResolver(
        world_repository=YamlWorldRepository(
            worlds_path=worlds_path,
        )
    )


def test_luxembourgish_world_resolves_from_runtime_configuration():
    resolver = create_world_resolver()

    context = resolver.resolve(
        "luxembourgish_world"
    )

    assert context.world_id == "luxembourgish_world"
    assert context.name == "Luxembourgish World"
    assert context.language_code == "lb"
    assert context.world_type == "language"
    assert context.learning_domain == "language_learning"

    assert context.language_policy is not None
    assert context.language_policy.mode == "target_language"
    assert context.language_policy.target_language == "lb"

    assert context.available_characters == (
        "yeti",
        "alix",
    )