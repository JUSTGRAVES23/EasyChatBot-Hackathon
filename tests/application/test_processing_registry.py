from app.application.privacy.processing_activity import ProcessingActivity
from app.application.privacy.processing_registry import ProcessingRegistry


def activity() -> ProcessingActivity:
    return ProcessingActivity(
        processing_id="PA-001",
        name="Test processing",
        purpose="Test purpose",
        data_categories=("conversation",),
        data_subjects=("learner",),
        source=("Telegram",),
        destinations=("runtime",),
        legal_basis="test",
        retention_id="RET-001",
        data_map_id="MAP-001",
        dpia_screening_id="DPIA-001",
        gdpr_references=("GDPR Art. 5",),
        security_controls=("access control",),
    )


def test_registry_registers_and_retrieves_activity():
    registry = ProcessingRegistry()
    item = activity()
    registry.register(item)

    assert registry.get("PA-001") is item
    assert registry.ids() == {"PA-001"}


def test_registry_rejects_duplicate_processing_id():
    registry = ProcessingRegistry([activity()])

    try:
        registry.register(activity())
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("Duplicate processing ID was accepted")

