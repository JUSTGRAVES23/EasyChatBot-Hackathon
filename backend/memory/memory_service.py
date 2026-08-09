"""
Memory Service.

Application service responsible for:

- saving memories
- retrieving memories
- preparing context for AI agents
"""


from datetime import datetime


from backend.memory.memory_record import (
    MemoryRecord,
)

from backend.memory.memory_store import (
    MemoryStore,
)


class MemoryService:
    """
    Controls memory operations.
    """


    def __init__(
        self,
        store=None,
    ):

        self.store = (
            store
            or MemoryStore()
        )


    def remember(
        self,
        user_id: str,
        category: str,
        content: str,
    ):

        record = MemoryRecord(
            user_id=user_id,
            category=category,
            content=content,
            created_at=datetime.utcnow(),
        )

        self.store.save(
            record
        )


    def recall(
        self,
        user_id: str,
    ):

        return self.store.get_by_user(
            user_id
        )