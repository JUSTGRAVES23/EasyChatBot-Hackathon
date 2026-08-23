from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProcessorRecord:
    processor_id: str
    provider_name: str
    role: str
    processor_agreement_art28: str
    hosting_location: str
    third_country: bool
    safeguard_art46_47: str | None
    dpo_status: str
    grc_status: str
    legal_status: str


class ProcessorRegistry:
    def __init__(self, records: list[ProcessorRecord] | None = None) -> None:
        self._records = {record.processor_id: record for record in records or []}

    def register(self, record: ProcessorRecord) -> None:
        if record.processor_id in self._records:
            raise ValueError(
                f"Processor already registered: {record.processor_id}"
            )
        self._records[record.processor_id] = record

    def get(self, processor_id: str) -> ProcessorRecord:
        return self._records[processor_id]

    def all(self) -> tuple[ProcessorRecord, ...]:
        return tuple(self._records.values())
