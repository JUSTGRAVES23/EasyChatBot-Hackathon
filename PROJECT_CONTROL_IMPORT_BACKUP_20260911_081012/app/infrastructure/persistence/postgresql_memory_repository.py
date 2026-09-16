from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.application.memory.memory_models import (
    ConversationMemory,
)

from app.application.memory.memory_repository import (
    ConversationMemoryRepository,
)

from .memory_records import (
    ConversationMemoryRecord,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)



class PostgreSQLConversationMemoryRepository(
    ConversationMemoryRepository
):
    """
    PostgreSQL implementation of conversation memory storage.

    Isolation boundary:

        telegram_user_id
                +
             world_id

    """

    def __init__(
        self,
        session_factory,
    ) -> None:

        self._session_factory = session_factory



    async def save(
        self,
        memory: ConversationMemory,
    ) -> ConversationMemory:

        with self._session_factory() as session:

            row = session.get(
                ConversationMemoryRecord,
                memory.memory_id,
            )


            if row is None:

                session.add(
                    ConversationMemoryRecord(
                        id=memory.memory_id,

                        telegram_user_id=(
                            memory.telegram_user_id
                        ),

                        world_id=(
                            memory.world_id
                        ),

                        memory_key=(
                            memory.memory_key
                        ),

                        memory_value=(
                            memory.memory_value
                        ),

                        created_at=(
                            memory.created_at
                        ),
                    )
                )


            else:

                row.memory_value = (
                    memory.memory_value
                )


            session.commit()


        return memory



    async def get_user_memories(
        self,
        *,
        telegram_user_id: str,
        world_id: str,
    ) -> list[ConversationMemory]:

        with self._session_factory() as session:

            rows = session.scalars(
                select(
                    ConversationMemoryRecord
                )
                .where(
                    ConversationMemoryRecord.telegram_user_id
                    == telegram_user_id
                )
                .where(
                    ConversationMemoryRecord.world_id
                    == world_id
                )
                .order_by(
                    ConversationMemoryRecord.created_at
                )
            ).all()


            return [
                _memory_from_record(row)
                for row in rows
            ]



    async def clear_user_memory(
        self,
        *,
        telegram_user_id: str,
        world_id: str,
    ) -> None:

        with self._session_factory() as session:

            rows = session.scalars(
                select(
                    ConversationMemoryRecord
                )
                .where(
                    ConversationMemoryRecord.telegram_user_id
                    == telegram_user_id
                )
                .where(
                    ConversationMemoryRecord.world_id
                    == world_id
                )
            ).all()


            for row in rows:
                session.delete(row)


            session.commit()



def _memory_from_record(
    row: ConversationMemoryRecord,
) -> ConversationMemory:

    return ConversationMemory(

        memory_id=row.id,

        telegram_user_id=(
            row.telegram_user_id
        ),

        world_id=(
            row.world_id
        ),

        memory_key=(
            row.memory_key
        ),

        memory_value=(
            row.memory_value
        ),

        created_at=(
            row.created_at
        ),
    )
