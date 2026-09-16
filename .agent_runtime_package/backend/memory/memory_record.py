"""
Memory Record Model.

Represents information stored
to personalise future interactions.
"""


from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MemoryRecord:
    """
    Single memory item.
    """

    user_id: str

    category: str

    content: str

    created_at: datetime