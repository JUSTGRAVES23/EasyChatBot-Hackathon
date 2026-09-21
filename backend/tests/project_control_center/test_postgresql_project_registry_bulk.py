from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.persistence.postgresql_project_registry import PostgreSQLProjectRegistry
from app.infrastructure.persistence.project_registry_records import ProjectRegistryRecord
from app.project_control_center.domain.models import ProjectDefinition


def make_registry() -> PostgreSQLProjectRegistry:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    ProjectRegistryRecord.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return PostgreSQLProjectRegistry(factory)


def test_create_many_is_atomic_for_duplicate_rows() -> None:
    registry = make_registry()
    projects = [
        ProjectDefinition(project_id="one", name="One"),
        ProjectDefinition(project_id="one", name="Duplicate"),
    ]

    with pytest.raises(ValueError, match="Project already exists"):
        registry.create_many(projects)

    assert registry.get("one") is None


def test_create_many_persists_all_rows() -> None:
    registry = make_registry()
    projects = [
        ProjectDefinition(project_id="one", name="One"),
        ProjectDefinition(project_id="two", name="Two"),
    ]

    result = registry.create_many(projects)

    assert [item.project_id for item in result] == ["one", "two"]
    assert registry.get("one") is not None
    assert registry.get("two") is not None


def test_upsert_many_updates_and_creates_in_one_operation() -> None:
    registry = make_registry()
    registry.save(ProjectDefinition(project_id="existing", name="Existing"))

    result = registry.upsert_many([
        ProjectDefinition(project_id="existing", name="Updated"),
        ProjectDefinition(project_id="new", name="New"),
    ])

    assert [item.project_id for item in result] == ["existing", "new"]
    assert registry.get("existing").name == "Updated"
    assert registry.get("new").name == "New"
