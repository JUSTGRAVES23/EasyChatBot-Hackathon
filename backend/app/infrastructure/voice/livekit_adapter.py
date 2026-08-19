"""
LiveKit Infrastructure Adapter.

Responsible for communication with LiveKit.

This layer is infrastructure only.

Responsibilities:
- Prepare LiveKit connection data.
- Abstract LiveKit provider details.
- Create room connection metadata.

Does NOT:
- Decide when a call starts.
- Manage learner logic.
- Execute AI agents.
- Store memory.
"""

from __future__ import annotations

import logging

from app.domain.uai.voice.voice_session import (
    VoiceSession,
)


logger = logging.getLogger(__name__)


class LiveKitAdapter:
    """
    Infrastructure adapter for LiveKit.

    Beta 1 implementation:
    - Provider abstraction only.
    - Real API connection added later.
    """

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
            Voice session information.

        Returns
        -------
        dict
            Provider-independent room data.
        """

        logger.info(
            "Preparing LiveKit room configuration",
            extra={
                "session_id": session.session_id,
                "room_name": session.room_name,
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
            "provider": "livekit",
        }