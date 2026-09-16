from app.infrastructure.persistence import model_registry
from app.infrastructure.persistence.database import Base
from app.infrastructure.persistence.learning_world_models import (
    LearningWorldModel,
)


def test_learning_world_model_uses_canonical_base_metadata() -> None:
    assert LearningWorldModel.metadata is Base.metadata


def test_learning_world_model_is_registered_in_canonical_metadata() -> None:
    assert "learning_worlds" in Base.metadata.tables
    assert Base.metadata.tables["learning_worlds"] is (
        LearningWorldModel.__table__
    )


def test_model_registry_exports_learning_world_model() -> None:
    assert model_registry.LearningWorldModel is LearningWorldModel


def test_learning_world_model_contains_runtime_world_mapping_column() -> None:
    table = Base.metadata.tables["learning_worlds"]

    assert "runtime_world_id" in table.columns
    assert table.columns["runtime_world_id"].nullable is True