from dataclasses import dataclass

@dataclass(frozen=True)
class MemoryCandidate:
    learner_hash:str
    category:str
    value:str
    confidence:float
