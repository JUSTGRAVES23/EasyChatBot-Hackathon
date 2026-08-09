"""
Memory Store.

Temporary in-memory implementation.

Future versions can replace this with:

- SQLite
- PostgreSQL
- Vector database
- Enterprise memory service
"""


from backend.memory.memory_record import (
    MemoryRecord,
)


class MemoryStore:
    """
    Stores user memories.
    """


    def __init__(self):

        self._records: list[
            MemoryRecord
        ] = []


    def save(
        self,
        record: MemoryRecord,
    ):

        self._records.append(
            record
        )


    def get_by_user(
        self,
        user_id: str,
    ) -> list[MemoryRecord]:

        return [
            record
            for record in self._records
            if record.user_id == user_id
        ]