from dataclasses import dataclass
import pytest
from app.application.world_catalogue.models import LearningWorldCatalogueEntry
from app.application.world_catalogue.service import LearningWorldCatalogueService

@dataclass
class FakeRepository:
    entry: LearningWorldCatalogueEntry | None
    def get_by_identifier(self, identifier: str):
        return self.entry

class FakeWorldResolver:
    def __init__(self, result=None):
        self.result = result
        self.requested_ids = []
    def resolve(self, world_id: str):
        self.requested_ids.append(world_id)
        return self.result

def make_entry(**changes):
    values = dict(identifier="french", name="French World", description="French language learning world.", language="fr", version="1.0.0", status="published", enabled=True, world_type="language", learning_domain="language_learning", runtime_world_id="french_world")
    values.update(changes)
    return LearningWorldCatalogueEntry(**values)

def test_resolve_uses_explicit_runtime_mapping():
    resolver = FakeWorldResolver("context")
    service = LearningWorldCatalogueService(repository=FakeRepository(make_entry()), world_resolver=resolver)
    assert service.resolve_runtime_world("french") == "context"
    assert resolver.requested_ids == ["french_world"]

def test_disabled_world_is_rejected():
    service = LearningWorldCatalogueService(repository=FakeRepository(make_entry(enabled=False)), world_resolver=FakeWorldResolver())
    with pytest.raises(ValueError, match="disabled"):
        service.resolve_runtime_world("french")

def test_unmapped_world_is_rejected():
    service = LearningWorldCatalogueService(repository=FakeRepository(make_entry(runtime_world_id=None)), world_resolver=FakeWorldResolver())
    with pytest.raises(ValueError, match="no runtime configuration"):
        service.resolve_runtime_world("french")

def test_unknown_world_is_rejected():
    service = LearningWorldCatalogueService(repository=FakeRepository(None), world_resolver=FakeWorldResolver())
    with pytest.raises(ValueError, match="not found"):
        service.resolve_runtime_world("french")

def test_blank_identifier_is_rejected():
    service = LearningWorldCatalogueService(repository=FakeRepository(None), world_resolver=FakeWorldResolver())
    with pytest.raises(ValueError, match="required"):
        service.resolve_runtime_world("   ")
