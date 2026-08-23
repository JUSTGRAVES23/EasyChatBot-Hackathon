from __future__ import annotations

from dataclasses import dataclass, field

from .processing_activity_record import ProcessingActivityRecord
from .data_processing_map import DataProcessingMap
from .retention_classification import RetentionClassification
from .privacy_evidence_record import PrivacyEvidenceRecord


@dataclass(slots=True)
class PrivacyOperationalRegister:
    """Governance register linking processing, flow, retention and evidence."""

    processing_activities: dict[str, ProcessingActivityRecord] = field(default_factory=dict)
    processing_maps: dict[str, DataProcessingMap] = field(default_factory=dict)
    retention: dict[str, RetentionClassification] = field(default_factory=dict)
    evidence: dict[str, PrivacyEvidenceRecord] = field(default_factory=dict)

    def add_processing_activity(self, record: ProcessingActivityRecord) -> None:
        if record.activity_id in self.processing_activities:
            raise ValueError(f"Duplicate processing activity: {record.activity_id}")
        self.processing_activities[record.activity_id] = record

    def add_processing_map(self, record: DataProcessingMap) -> None:
        if record.map_id in self.processing_maps:
            raise ValueError(f"Duplicate processing map: {record.map_id}")
        if record.processing_activity_id not in self.processing_activities:
            raise ValueError("Processing activity must exist before data map.")
        self.processing_maps[record.map_id] = record

    def add_retention(self, record: RetentionClassification) -> None:
        if record.classification_id in self.retention:
            raise ValueError(f"Duplicate retention classification: {record.classification_id}")
        self.retention[record.classification_id] = record

    def add_evidence(self, record: PrivacyEvidenceRecord) -> None:
        if record.evidence_id in self.evidence:
            raise ValueError(f"Duplicate evidence record: {record.evidence_id}")
        if record.activity_id not in self.processing_activities:
            raise ValueError("Processing activity must exist before evidence.")
        self.evidence[record.evidence_id] = record
