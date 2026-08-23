from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DPIAScreening:
    screening_id: str
    processing_id: str
    overall_risk: str
    dpia_required: str
    dpo_assessment: str
    grc_assessment: str
    status: str


class DPIAScreeningRegistry:
    def __init__(self, screenings: list[DPIAScreening] | None = None) -> None:
        self._screenings = {
            screening.processing_id: screening
            for screening in screenings or []
        }

    def register(self, screening: DPIAScreening) -> None:
        if screening.processing_id in self._screenings:
            raise ValueError(
                f"DPIA screening already exists for: {screening.processing_id}"
            )
        self._screenings[screening.processing_id] = screening

    def get(self, processing_id: str) -> DPIAScreening:
        return self._screenings[processing_id]

    def all(self) -> tuple[DPIAScreening, ...]:
        return tuple(self._screenings.values())
