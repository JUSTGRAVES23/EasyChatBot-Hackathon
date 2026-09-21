from uuid import UUID, uuid4

import pytest

from app.application.world_catalogue.models import (
    LearningWorldCatalogueEntry,
)


def values() -> dict:
    return {
        "id": uuid4(),
        "identifier": "french",
        "name": "French World",
        "description": "French language learning world.",
        "language": "fr",
        "version": "1.0.0",
        "status": "published",
        "enabled": True,
        "world_type": "language",
        "learning_domain": "language_learning",
        "runtime_world_id": "french_world",
    }


def test_authoritative_world_id_is_preserved() -> None:
    world_id = uuid4()

    data = values()
    data["id"] = world_id

    entry = LearningWorldCatalogueEntry(**data)

    assert entry.id == world_id
    assert isinstance(entry.id, UUID)


def test_invalid_world_id_is_rejected() -> None:
    data = values()
    data["id"] = "not-a-uuid"

    with pytest.raises(
        ValueError,
        match="id must be a UUID",
    ):
        LearningWorldCatalogueEntry(**data)


def test_runtime_mapping_may_be_none() -> None:
    data = values()
    data["runtime_world_id"] = None

    entry = LearningWorldCatalogueEntry(**data)

    assert entry.runtime_world_id is None


@pytest.mark.parametrize(
    "field",
    [
        "identifier",
        "name",
        "version",
        "status",
        "world_type",
        "learning_domain",
    ],
)
def test_required_text_fields_reject_blank(field: str) -> None:
    data = values()
    data[field] = "   "

    with pytest.raises(ValueError):
        LearningWorldCatalogueEntry(**data)


def test_blank_runtime_mapping_is_rejected() -> None:
    data = values()
    data["runtime_world_id"] = "   "

    with pytest.raises(
        ValueError,
        match="runtime_world_id",
    ):
        LearningWorldCatalogueEntry(**data)
