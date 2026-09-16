"""
LiveKit Infrastructure Adapter.

Infrastructure boundary for LiveKit room configuration.

Responsibilities:
- Translate voice session information into
  LiveKit provider configuration.
- Keep LiveKit-specific details inside infrastructure.
- Prepare provider connection metadata.

Does NOT:
- Decide when a call starts.
- Manage learner business logic.
- Execute AI agents.
- Manage application lifecycle.
- Persist data.
- Generate participant tokens.
"""

from __future__ import annotations


import logging


from app.domain.uai.voice.voice_session import (
    VoiceSession,
)


logger = logging.getLogger(
    __name__
)



class LiveKitAdapter:
    """
    Infrastructure adapter for LiveKit.

    Converts the provider-independent voice session
    into LiveKit room configuration.

    Token generation is deliberately handled by
    LiveKitTokenService.
    """



    provider = "livekit"



    def create_room_configuration(
        self,
        *,
        session: VoiceSession,
    ) -> dict[str, str]:
        """
        Prepare LiveKit room configuration.

        Parameters
        ----------
        session:
            Provider-independent voice session.

        Returns
        -------
        dict[str, str]
            LiveKit room metadata.
        """



        if not session.room_name.strip():

            raise ValueError(
                "Voice room name cannot be empty."
            )



        if not session.character_id.strip():

            raise ValueError(
                "Voice session character id "
                "cannot be empty."
            )



        logger.info(
            "Preparing LiveKit room configuration",
            extra={
                "session_id": (
                    session.session_id
                ),
                "room_name": (
                    session.room_name
                ),
                "character_id": (
                    session.character_id
                ),
                "language_code": (
                    session.language_code
                ),
            },
        )



        return {
            "room_name": (
                session.room_name
            ),
            "character_id": (
                session.character_id
            ),
            "language_code": (
                session.language_code
            ),
            "provider": self.provider,
        }



__all__ = [
    "LiveKitAdapter",
]
