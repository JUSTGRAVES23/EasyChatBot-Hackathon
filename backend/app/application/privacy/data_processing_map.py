from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DataProcessingMapEntry:
    """Describes the operational data flow for one processing activity."""

    map_id: str
    processing_id: str
    source: str
    input_data: tuple[str, ...]
    runtime_processing: tuple[str, ...]
    pseudonymisation: str
    persistence: tuple[str, ...]
    destinations: tuple[str, ...]
    third_country_transfer: bool
    transfer_safeguard: str | None = None


class DataProcessingMap:
    def __init__(self, entries: list[DataProcessingMapEntry] | None = None) -> None:
        self._entries = {entry.processing_id: entry for entry in entries or []}

    def add(self, entry: DataProcessingMapEntry) -> None:
        if entry.processing_id in self._entries:
            raise ValueError(
                f"Data map already exists for: {entry.processing_id}"
            )
        self._entries[entry.processing_id] = entry

    def get(self, processing_id: str) -> DataProcessingMapEntry:
        return self._entries[processing_id]

    def all(self) -> tuple[DataProcessingMapEntry, ...]:
        return tuple(self._entries.values())
