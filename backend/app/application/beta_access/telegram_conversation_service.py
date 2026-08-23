from __future__ import annotations


import secrets


from datetime import datetime, timezone
from typing import Any


from backend.app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)


from backend.app.application.conversation.conversation_event_models import (
    ConversationEvent,
)


from backend.app.application.conversation_quality.conversation_event_validator import (
    ConversationEventValidator,
)


from backend.app.application.privacy.privacy_identifier_service import (
    PrivacyIdentifierService,
)





class TelegramConversationService:
    """
    Telegram conversation application service.


    Responsibilities:

    - receive Telegram messages
    - create conversation events
    - validate privacy controls
    - pseudonymise identity
    - delegate execution to ConversationRuntime


    Does NOT:

    - manage Telegram transport
    - manage authorization
    - create memories
    - analyse learning behaviour


    Future:

        conversation_events
                |
                v
          Memory Engine
                |
                v
        Learning Personalisation
    """



    def __init__(
        self,
        *,
        conversation_runtime: ConversationRuntime,
        conversation_event_repository: Any,
        privacy_identifier_service: PrivacyIdentifierService,
        conversation_event_validator: ConversationEventValidator,
    ) -> None:


        if conversation_runtime is None:

            raise ValueError(
                "conversation_runtime cannot be None."
            )


        if conversation_event_repository is None:

            raise ValueError(
                "conversation_event_repository cannot be None."
            )


        if privacy_identifier_service is None:

            raise ValueError(
                "privacy_identifier_service cannot be None."
            )


        if conversation_event_validator is None:

            raise ValueError(
                "conversation_event_validator cannot be None."
            )



        self._runtime = conversation_runtime

        self._events = conversation_event_repository

        self._privacy = privacy_identifier_service

        self._validator = conversation_event_validator






    async def handle_telegram_message(
        self,
        *,
        telegram_user_id: int,
        message: str,
    ) -> str:



        if not message or not message.strip():

            raise ValueError(
                "Telegram message cannot be empty."
            )



        world_id = "world-fr"

        character = "Alix"

        level = "B1"



        telegram_user_hash = (

            self._privacy.pseudonymize_identifier(

                str(telegram_user_id)

            )

        )



        conversation_id = (

            f"telegram-{telegram_user_hash[:16]}"

        )




        metadata = {

            "world_id": world_id,

            "character": character,

            "level": level,

            "source": "telegram_beta",

            "privacy_hash_version": "v1",

            "retention_policy_id":
                "conversation_learning_default",

        }




        #
        # Validate BEFORE persistence
        #

        self._validator.validate(

            content=message,

            metadata=metadata,

            telegram_user_hash=telegram_user_hash,

        )





        await self._events.save(

            ConversationEvent(

                event_id=secrets.token_hex(16),


                conversation_id=conversation_id,


                telegram_user_hash=telegram_user_hash,


                world_id=world_id,


                channel="telegram",


                role="user",


                content=message,


                metadata=metadata,


                created_at=datetime.now(
                    timezone.utc
                ),

            )

        )






        response = await self._runtime.respond(

            character_instruction=(

                "You are EasyChatBot Academy, "

                "a friendly French learning assistant. "

                "Help the learner practise naturally."

            ),


            learner_message=message,

        )





        self._validator.validate(

            content=response,

            metadata=metadata,

            telegram_user_hash=telegram_user_hash,

        )





        await self._events.save(

            ConversationEvent(

                event_id=secrets.token_hex(16),


                conversation_id=conversation_id,


                telegram_user_hash=telegram_user_hash,


                world_id=world_id,


                channel="telegram",


                role="assistant",


                content=response,


                metadata=metadata,


                created_at=datetime.now(
                    timezone.utc
                ),

            )

        )



        return response