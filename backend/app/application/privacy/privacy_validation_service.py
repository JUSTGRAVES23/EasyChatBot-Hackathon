from __future__ import annotations

from dataclasses import dataclass

from .data_processing_map import DataProcessingMap
from .dpia_screening import DPIAScreeningRegistry
from .processing_registry import ProcessingRegistry
from .processor_registry import ProcessorRegistry
from .retention_registry import RetentionRegistry


@dataclass(frozen=True, slots=True)
class PrivacyValidationResult:
    checks: int
    passed: int
    failures: tuple[str, ...]

    @property
    def blocking_failures(self) -> int:
        return len(self.failures)

    @property
    def status(self) -> str:
        return "PASS" if not self.failures else "FAIL"


class PrivacyValidationService:
    """Deterministic privacy/GRC consistency validation.

    It detects missing/inconsistent governance evidence. It never makes
    legal decisions or grants DPO/GRC approval.
    """

    def __init__(
        self,
        *,
        processing_registry: ProcessingRegistry,
        data_processing_map: DataProcessingMap,
        retention_registry: RetentionRegistry,
        processor_registry: ProcessorRegistry,
        dpia_registry: DPIAScreeningRegistry,
    ) -> None:
        self._processing = processing_registry
        self._maps = data_processing_map
        self._retention = retention_registry
        self._processors = processor_registry
        self._dpia = dpia_registry

    def validate(self) -> PrivacyValidationResult:
        failures: list[str] = []
        checks = 0

        for activity in self._processing.all():
            checks += 1
            if not activity.purpose or not activity.data_categories:
                failures.append(
                    f"{activity.processing_id}: purpose/data categories incomplete"
                )

            checks += 1
            try:
                data_map = self._maps.get(activity.processing_id)
                if data_map.map_id != activity.data_map_id:
                    failures.append(
                        f"{activity.processing_id}: data map reference mismatch"
                    )
            except KeyError:
                failures.append(
                    f"{activity.processing_id}: missing data processing map"
                )

            checks += 1
            try:
                self._retention.get(activity.retention_id)
            except KeyError:
                failures.append(
                    f"{activity.processing_id}: missing retention rule"
                )

            checks += 1
            for processor_id in activity.processor_ids:
                try:
                    self._processors.get(processor_id)
                except KeyError:
                    failures.append(
                        f"{activity.processing_id}: missing processor {processor_id}"
                    )

            checks += 1
            try:
                screening = self._dpia.get(activity.processing_id)
                if screening.screening_id != activity.dpia_screening_id:
                    failures.append(
                        f"{activity.processing_id}: DPIA screening reference mismatch"
                    )
            except KeyError:
                failures.append(
                    f"{activity.processing_id}: missing DPIA screening"
                )

            checks += 1
            if not activity.legal_basis:
                failures.append(
                    f"{activity.processing_id}: legal basis missing"
                )

            checks += 1
            if not activity.gdpr_references:
                failures.append(
                    f"{activity.processing_id}: GDPR references missing"
                )

            checks += 1
            if not activity.security_controls:
                failures.append(
                    f"{activity.processing_id}: security controls missing"
                )

            checks += 1
            if activity.approval_status not in {"PENDING", "APPROVED"}:
                failures.append(
                    f"{activity.processing_id}: invalid approval status"
                )

        # Two registry-level integrity checks.
        checks += 1
        if len(self._processing.ids()) != len(self._processing.all()):
            failures.append("duplicate processing registry identifiers")

        checks += 1
        map_ids = {entry.processing_id for entry in self._maps.all()}
        missing_maps = self._processing.ids() - map_ids
        if missing_maps:
            failures.append(
                f"processing activities missing maps: {sorted(missing_maps)}"
            )

        return PrivacyValidationResult(
            checks=checks,
            passed=checks - len(failures),
            failures=tuple(failures),
        )
