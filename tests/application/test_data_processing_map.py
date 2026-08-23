from backend.app.application.privacy.data_processing_map import (
    DataProcessingMap,
    DataProcessingMapEntry,
)


def test_data_processing_map_registers_entry():
    registry = DataProcessingMap()
    entry = DataProcessingMapEntry(
        map_id="MAP-001",
        processing_id="PA-001",
        source="Telegram",
        input_data=("conversation",),
        runtime_processing=("runtime",),
        pseudonymisation="hash",
        persistence=("event store",),
        destinations=("runtime",),
        third_country_transfer=False,
    )

    registry.add(entry)

    assert registry.get("PA-001") == entry
    assert registry.all() == (entry,)


def test_data_processing_map_rejects_duplicate_processing_id():
    entry = DataProcessingMapEntry(
        map_id="MAP-001",
        processing_id="PA-001",
        source="Telegram",
        input_data=("conversation",),
        runtime_processing=("runtime",),
        pseudonymisation="hash",
        persistence=("event store",),
        destinations=("runtime",),
        third_country_transfer=False,
    )
    registry = DataProcessingMap([entry])

    try:
        registry.add(entry)
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("Duplicate processing map was accepted")
