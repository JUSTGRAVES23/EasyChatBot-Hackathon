from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.domain.study_material.study_material import (
    StudyMaterial,
    StudyMaterialStatus,
    StudyMaterialType,
)


def make_material(
    *,
    material_id=None,
    world_id="french_world",
    title="French Greetings",
    description="Basic French greetings.",
    material_type=StudyMaterialType.LESSON,
    status=StudyMaterialStatus.PUBLISHED,
    display_order=1,
    created_at=None,
    updated_at=None,
):
    created_at = created_at or datetime.now(timezone.utc)
    updated_at = updated_at or created_at

    return StudyMaterial(
        material_id=material_id or uuid4(),
        world_id=world_id,
        title=title,
        description=description,
        material_type=material_type,
        status=status,
        display_order=display_order,
        created_at=created_at,
        updated_at=updated_at,
    )


def test_valid_study_material_is_created():
    material = make_material()

    assert material.world_id == "french_world"
    assert material.title == "French Greetings"
    assert material.description == "Basic French greetings."
    assert material.material_type is StudyMaterialType.LESSON
    assert material.status is StudyMaterialStatus.PUBLISHED
    assert material.display_order == 1


def test_study_material_is_immutable():
    material = make_material()

    with pytest.raises(AttributeError):
        material.title = "Changed"


def test_material_id_must_be_uuid():
    with pytest.raises(
        ValueError,
        match="material_id must be a UUID",
    ):
        make_material(material_id="material-1")


def test_world_id_is_required():
    with pytest.raises(
        ValueError,
        match="world_id cannot be empty",
    ):
        make_material(world_id="   ")


def test_world_id_must_be_string():
    with pytest.raises(
        ValueError,
        match="world_id must be a string",
    ):
        make_material(world_id=123)


def test_title_is_required():
    with pytest.raises(
        ValueError,
        match="title cannot be empty",
    ):
        make_material(title="   ")


def test_title_must_be_string():
    with pytest.raises(
        ValueError,
        match="title must be a string",
    ):
        make_material(title=123)


def test_description_may_be_none():
    material = make_material(description=None)

    assert material.description is None


def test_description_must_be_string_when_present():
    with pytest.raises(
        ValueError,
        match="description must be a string or None",
    ):
        make_material(description=123)


@pytest.mark.parametrize(
    "material_type",
    [
        StudyMaterialType.READING,
        StudyMaterialType.LESSON,
        StudyMaterialType.EXERCISE,
    ],
)
def test_supported_material_types_are_accepted(material_type):
    material = make_material(
        material_type=material_type,
    )

    assert material.material_type is material_type


def test_material_type_must_use_controlled_enum():
    with pytest.raises(
        ValueError,
        match="material_type must be a StudyMaterialType",
    ):
        make_material(material_type="VIDEO")


@pytest.mark.parametrize(
    "status",
    [
        StudyMaterialStatus.DRAFT,
        StudyMaterialStatus.PUBLISHED,
        StudyMaterialStatus.ARCHIVED,
    ],
)
def test_supported_statuses_are_accepted(status):
    material = make_material(status=status)

    assert material.status is status


def test_status_must_use_controlled_enum():
    with pytest.raises(
        ValueError,
        match="status must be a StudyMaterialStatus",
    ):
        make_material(status="DELETED")


def test_display_order_may_be_zero():
    material = make_material(display_order=0)

    assert material.display_order == 0


def test_display_order_cannot_be_negative():
    with pytest.raises(
        ValueError,
        match="display_order cannot be negative",
    ):
        make_material(display_order=-1)


def test_display_order_must_be_integer():
    with pytest.raises(
        ValueError,
        match="display_order must be an integer",
    ):
        make_material(display_order=1.5)


def test_boolean_is_not_valid_display_order():
    with pytest.raises(
        ValueError,
        match="display_order must be an integer",
    ):
        make_material(display_order=True)


def test_created_at_must_be_datetime():
    with pytest.raises(
        ValueError,
        match="created_at must be a datetime",
    ):
        make_material(created_at="2026-09-17")


def test_updated_at_must_be_datetime():
    with pytest.raises(
        ValueError,
        match="updated_at must be a datetime",
    ):
        make_material(updated_at="2026-09-17")


def test_updated_at_cannot_be_before_created_at():
    created_at = datetime.now(timezone.utc)
    updated_at = created_at - timedelta(seconds=1)

    with pytest.raises(
        ValueError,
        match="updated_at cannot be earlier than created_at",
    ):
        make_material(
            created_at=created_at,
            updated_at=updated_at,
        )


def test_material_has_no_learner_identity():
    material = make_material()

    assert not hasattr(material, "learner_id")
    assert not hasattr(material, "telegram_user_id")
    assert not hasattr(material, "telegram_user_hash")
    assert not hasattr(material, "conversation_id")


def test_material_has_no_content_storage_field():
    material = make_material()

    assert not hasattr(material, "content")
    assert not hasattr(material, "content_blob")
    assert not hasattr(material, "storage_key")
    assert not hasattr(material, "embedding")


def test_material_has_no_ai_runtime_dependency():
    material = make_material()

    assert not hasattr(material, "llm_provider")
    assert not hasattr(material, "model")
    assert not hasattr(material, "runtime_context")
    assert not hasattr(material, "rag_context")