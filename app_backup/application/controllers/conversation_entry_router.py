"""
===============================================================================

EasyChatBot Hackathon

Conversation Entry Router

Layer:
Application Layer

Purpose:
Route incoming conversation requests.

Responsibilities:
- Validate incoming message.
- Identify command intent.
- Route to approved application handlers.

Does NOT:
- Execute AI providers.
- Execute agents.
- Persist memory.
- Manage infrastructure.

===============================================================================
"""

from __future__ import annotations


import logging


from dataclasses import dataclass



logger = logging.getLogger(__name__)




@dataclass(frozen=True)
class ConversationRequest:
    """
    Incoming conversation request.
    """

    message: str

    user_id: str | None = None

    character_id: str | None = None




@dataclass(frozen=True)
class ConversationResponse:
    """
    Router response contract.
    """

    route: str

    message: str




class ConversationEntryRouter:
    """
    Application entry routing boundary.

    Keeps transport/application separation.
    """



    DAILY_COMMAND = "/daily"

    WEEKLY_COMMAND = "/weekly"



    def __init__(
        self,
        *,
        conversation_handler=None,
        command_handler=None,
    ) -> None:
        """
        Initialise router dependencies.
        """

        self._conversation_handler = (
            conversation_handler
        )

        self._command_handler = (
            command_handler
        )


        logger.info(
            "ConversationEntryRouter initialised."
        )



    def route(
        self,
        request: ConversationRequest,
    ) -> ConversationResponse:
        """
        Route incoming message.
        """


        if not request.message.strip():

            raise ValueError(
                "message cannot be empty."
            )


        message = (
            request.message
            .strip()
            .lower()
        )



        if message in {
            self.DAILY_COMMAND,
            self.WEEKLY_COMMAND,
        }:

            logger.debug(
                "Routing command: %s",
                message,
            )


            if self._command_handler:

                return self._command_handler(
                    request
                )


            return ConversationResponse(
                route="command",
                message=message,
            )



        logger.debug(
            "Routing conversation message."
        )


        if self._conversation_handler:

            return self._conversation_handler(
                request
            )


        return ConversationResponse(
            route="conversation",
            message=request.message,
        )



__all__ = [
    "ConversationEntryRouter",
    "ConversationRequest",
    "ConversationResponse",
]