from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Processor:
    provider: str
    country: str
    data_location: str
    scc_tia: str | None
    dpa: str | None


class ProcessorRegistryService:
    def __init__(self):
        self.processors: list[Processor] = []

    def register(self, processor: Processor):
        self.processors.append(processor)
