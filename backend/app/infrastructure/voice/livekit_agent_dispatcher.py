"""
LiveKit Agent Dispatcher.

Infrastructure adapter responsible for dispatching
an approved EasyChatBot voice call to the LiveKit
realtime agent worker.

Responsibilities:
- Create a LiveKit agent dispatch.
- Target the EasyChatBot voice worker.
- Pass approved voice-call metadata to the worker.
- Keep LiveKit API details inside infrastructure.

Does NOT:
- Decide whether a call is authorized.
- Create voice-call business state.
- Manage application lifecycle.
- Resolve worlds or characters.
- Execute AI agents.
- Persist conversations.
- Generate participant tokens.
"""

from __future__ import annotations


import json
import logging
import os


from dataclasses import dataclass


from livekit import api


logger = logging.getLogger(
    __name__
)


@dataclass(
    frozen=True,
    slots=True,
)
class LiveKitAgentDispatcher:
    """
    Infrastructure adapter for LiveKit Agent dispatch.

    The application layer supplies an already-approved
    voice-call context. This adapter translates that
    context into a LiveKit AgentDispatch request.

    LiveKit credentials are read from the environment
    and remain inside the infrastructure boundary.
    """

    agent_name: str = "easychatbot-voice"


    def dispatch(
        self,
        *,
        room_name: str,
        learner_id: str,
        world_id: str,
        character_id: str,
        language_code: str,
    ) -> str:
        """
        Dispatch the EasyChatBot voice agent to a room.

        Parameters
        ----------
        room_name:
            LiveKit room that the agent must join.

        learner_id:
            Approved learner identifier.

        world_id:
            Active learning world.

        character_id:
            Approved AI character.

        language_code:
            Active interaction language.

        Returns
        -------
        str
            LiveKit dispatch identifier.

        Raises
        ------
        ValueError
            If required values are empty or credentials
            are not configured.
        """

        self._validate_required_value(
            room_name,
            "room_name",
        )

        self._validate_required_value(
            learner_id,
            "learner_id",
        )

        self._validate_required_value(
            world_id,
            "world_id",
        )

        self._validate_required_value(
            character_id,
            "character_id",
        )

        self._validate_required_value(
            language_code,
            "language_code",
        )


        api_key = os.getenv(
            "LIVEKIT_API_KEY",
        )

        api_secret = os.getenv(
            "LIVEKIT_API_SECRET",
        )

        livekit_url = os.getenv(
            "LIVEKIT_URL",
        )


        if not api_key:
            raise ValueError(
                "LIVEKIT_API_KEY is not configured."
            )


        if not api_secret:
            raise ValueError(
                "LIVEKIT_API_SECRET is not configured."
            )


        if not livekit_url:
            raise ValueError(
                "LIVEKIT_URL is not configured."
            )


        metadata = {
            "learner_id": learner_id.strip(),
            "world_id": world_id.strip(),
            "character_id": character_id.strip(),
            "language_code": language_code.strip(),
        }


        metadata_json = json.dumps(
            metadata,
            separators=(
                ",",
                ":",
            ),
        )


        logger.info(
            "Dispatching EasyChatBot LiveKit agent",
            extra={
                "room_name": room_name,
                "agent_name": self.agent_name,
                "learner_id": learner_id,
                "world_id": world_id,
                "character_id": character_id,
                "language_code": language_code,
            },
        )


        livekit_api = api.LiveKitAPI(
            url=livekit_url,
            api_key=api_key,
            api_secret=api_secret,
        )


        try:
            dispatch = (
                livekit_api
                .agent_dispatch
                .create_dispatch(
                    api.CreateAgentDispatchRequest(
                        agent_name=(
                            self.agent_name
                        ),
                        room=room_name.strip(),
                        metadata=metadata_json,
                    )
                )
            )


            logger.info(
                "LiveKit agent dispatch created",
                extra={
                    "dispatch_id": (
                        dispatch.id
                    ),
                    "room_name": room_name,
                    "agent_name": (
                        self.agent_name
                    ),
                },
            )


            return dispatch.id

        finally:
            livekit_api.aclose()


    @staticmethod
    def _validate_required_value(
        value: str,
        field_name: str,
    ) -> None:
        """
        Validate a required string field.
        """

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                f"{field_name} must be a string."
            )


        if not value.strip():
            raise ValueError(
                f"{field_name} cannot be empty."
            )


__all__ = [
    "LiveKitAgentDispatcher",
]