"""
Voice Session Service.

Application service responsible for creating
voice interaction sessions.

Responsibilities:
- Create VoiceSession domain objects.
- Translate InteractionContext into
  voice session state.
- Prepare data for voice infrastructure.

Does NOT:
- Connect to LiveKit.
- Create rooms.
- Generate tokens.
- Handle audio.
"""

from __future__ import annotations

import uuid
import logging

from app.domain.uai.context.interaction_context import (
    InteractionContext,
)

from app.domain.uai.voice.voice_session import (
    VoiceSession,
)


logger = logging.getLogger(__name__)


class VoiceSessionService:
    """
    Creates voice sessions from interaction context.
    """

    def create_session(
        self,
        *,
        interaction_context: InteractionContext,
    ) -> VoiceSession:
        """
        Create a new voice session.

        Parameters
        ----------
        interaction_context:
            Complete UAI interaction context.

        Returns
        -------
        VoiceSession
            Created voice session.
        """

        session_id = (
            str(
                uuid.uuid4()
            )
        )


        character_id = (
            interaction_context
            .character
            .character_id
        )


        language_code = (
            interaction_context
            .world
            .language_code
        )


        room_name = (
            f"{character_id}-{session_id[:8]}"
        )


        session = VoiceSession(
            session_id=session_id,
            room_name=room_name,
            character_id=character_id,
            language_code=language_code,
        )


        logger.info(
            "Voice session created",
            extra={
                "session_id": session_id,
                "character_id": character_id,
            },
        )


        return session
