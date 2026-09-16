import pytest
from app.application.world_catalogue.models import LearningWorldCatalogueEntry

def values():
    return dict(identifier="french", name="French World", description="French language learning world.", language="fr", version="1.0.0", status="published", enabled=True, world_type="language", learning_domain="language_learning", runtime_world_id="french_world")

def test_runtime_mapping_may_be_none():
    data = values(); data["runtime_world_id"] = None
    assert LearningWorldCatalogueEntry(**data).runtime_world_id is None

@pytest.mark.parametrize("field", ["identifier", "name", "version", "status", "world_type", "learning_domain"])
def test_required_text_fields_reject_blank(field):
    data = values(); data[field] = "   "
    with pytest.raises(ValueError):
        LearningWorldCatalogueEntry(**data)

def test_blank_runtime_mapping_is_rejected():
    data = values(); data["runtime_world_id"] = "   "
    with pytest.raises(ValueError, match="runtime_world_id"):
        LearningWorldCatalogueEntry(**data)
