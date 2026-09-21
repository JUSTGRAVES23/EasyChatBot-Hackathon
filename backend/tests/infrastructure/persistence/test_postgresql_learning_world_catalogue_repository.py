"""Unit tests for the PostgreSQL Learning World catalogue repository."""

from uuid import uuid4

import pytest

from app.infrastructure.persistence.learning_world_models import LearningWorldModel
from app.infrastructure.persistence.postgresql_learning_world_catalogue_repository import (
    PostgreSQLLearningWorldCatalogueRepository,
)


class FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def all(self):
        return list(self._value)

    def __iter__(self):
        return iter(self._value)


class FakeSession:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def scalar(self, statement):
        return self.row

    def scalars(self, statement):
        return FakeScalarResult(self.rows)


class FakeSessionFactory:
    def __init__(self, session):
        self.session = session

    def __call__(self):
        return self.session


def make_row(world_id):
    return LearningWorldModel(
        id=world_id,
        identifier="french_world",
        name="French World",
        description="French learning World for testing.",
        language="French",
        version="1.0",
        status="ACTIVE",
        enabled=True,
        world_type="LANGUAGE",
        learning_domain="LANGUAGE_LEARNING",
        runtime_world_id="french-runtime",
    )


def test_get_by_id_returns_authoritative_world():
    world_id = uuid4()
    row = make_row(world_id)

    repository = PostgreSQLLearningWorldCatalogueRepository(
        session_factory=FakeSessionFactory(
            FakeSession(row=row)
        )
    )

    result = repository.get_by_id(world_id)

    assert result is not None
    assert result.id == world_id
    assert result.identifier == "french_world"


def test_get_by_id_returns_none_for_unknown_world():
    world_id = uuid4()

    repository = PostgreSQLLearningWorldCatalogueRepository(
        session_factory=FakeSessionFactory(
            FakeSession(row=None)
        )
    )

    assert repository.get_by_id(world_id) is None


def test_get_by_id_requires_uuid():
    repository = PostgreSQLLearningWorldCatalogueRepository(
        session_factory=FakeSessionFactory(
            FakeSession()
        )
    )

    with pytest.raises(
        ValueError,
        match="world_id must be a UUID",
    ):
        repository.get_by_id("not-a-uuid")
