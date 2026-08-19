"""
Voice Session Orchestrator.

Coordinates the creation of a complete
voice interaction preparation flow.

Responsibilities:
- Create voice session.
- Prepare voice infrastructure.
- Return call configuration.

Does NOT:
- Run AI agents.
- Handle audio streams.
- Manage LiveKit lifecycle.
"""

from __future__ import annotations

import logging

from app.application.uai.voice.voice_session_service import (
    VoiceSessionService,
)

from app.domain.uai.context.interaction_context import (
    InteractionContext,
)

from app.infrastructure.voice.livekit_adapter import (
    LiveKitAdapter,
)


logger = logging.getLogger(__name__)


class VoiceSessionOrchestrator:
    """
    Coordinates voice session preparation.
    """

    def __init__(
        self,
        *,
        voice_session_service: VoiceSessionService,
        livekit_adapter: LiveKitAdapter,
    ) -> None:

        self._voice_session_service = (
            voice_session_service
        )

        self._livekit_adapter = (
            livekit_adapter
        )


    def prepare_session(
        self,
        *,
        interaction_context: InteractionContext,
    ) -> dict[str, str]:
        """
        Prepare a voice session.

        Returns provider configuration
        required to start a call.
        """

        session = (
            self._voice_session_service
            .create_session(
                interaction_context=interaction_context,
            )
        )


        configuration = (
            self._livekit_adapter
            .create_room_configuration(
                session=session,
            )
        )


        logger.info(
            "Voice session prepared",
            extra={
                "session_id": session.session_id,
            },
        )


        return configuration