from __future__ import annotations


from sqlalchemy import select


from backend.app.application.conversation.conversation_event_models import (
    ConversationEvent,
)


from backend.app.application.conversation.conversation_event_repository import (
    ConversationEventRepository,
)


from .conversation_event_records import (
    ConversationEventRecord,
)





class PostgreSQLConversationEventRepository(
    ConversationEventRepository
):
    """
    PostgreSQL implementation of conversation event storage.


    Privacy isolation:

        telegram_user_hash
                +
          conversation_id
                +
             world_id


    Responsibility:

    - persist conversation events
    - retrieve conversation history


    Does NOT:

    - validate business rules
    - create memories
    - analyse learning behaviour
    - create RAG knowledge
    """



    def __init__(
        self,
        session_factory,
    ) -> None:


        if session_factory is None:

            raise ValueError(
                "session_factory cannot be None."
            )


        self._session_factory = session_factory






    async def save(
        self,
        event: ConversationEvent,
    ) -> ConversationEvent:


        with self._session_factory() as session:


            record = ConversationEventRecord(


                id=event.event_id,


                conversation_id=(
                    event.conversation_id
                ),


                telegram_user_hash=(
                    event.telegram_user_hash
                ),


                world_id=(
                    event.world_id
                ),


                channel=(
                    event.channel
                ),


                role=(
                    event.role
                ),


                content=(
                    event.content
                ),


                metadata_json=(
                    event.metadata
                ),


                created_at=(
                    event.created_at
                ),
            )


            session.add(record)

            session.commit()



        return event







    async def get_recent(
        self,
        *,
        telegram_user_hash: str,
        world_id: str,
        limit: int = 20,
    ) -> list[ConversationEvent]:


        with self._session_factory() as session:


            rows = session.scalars(


                select(
                    ConversationEventRecord
                )


                .where(

                    ConversationEventRecord.telegram_user_hash
                    ==
                    telegram_user_hash

                )


                .where(

                    ConversationEventRecord.world_id
                    ==
                    world_id

                )


                .order_by(

                    ConversationEventRecord.created_at.desc()

                )


                .limit(limit)


            ).all()



        return [

            _event_from_record(row)

            for row in reversed(rows)

        ]








def _event_from_record(
    row: ConversationEventRecord,
) -> ConversationEvent:


    return ConversationEvent(

        event_id=row.id,


        conversation_id=(
            row.conversation_id
        ),


        telegram_user_hash=(
            row.telegram_user_hash
        ),


        world_id=(
            row.world_id
        ),


        channel=(
            row.channel
        ),


        role=(
            row.role
        ),


        content=(
            row.content
        ),


        metadata=(
            row.metadata_json
        ),


        created_at=(
            row.created_at
        ),
    )