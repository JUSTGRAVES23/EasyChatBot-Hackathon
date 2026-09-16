"""
Voice Call Execution Runtime.

Runtime execution coordinator for
AI character voice calls.

Responsibilities:
- Execute prepared voice call sessions.
- Coordinate execution lifecycle.
- Validate execution context.
- Provide runtime boundaries.

Does NOT:
- Handle HTTP.
- Persist sessions.
- Manage authentication.
- Own LiveKit connections.
- Select providers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)
from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)
from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)


logger = logging.getLogger(__name__)


@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallExecutionRuntime:
    """
    Executes prepared voice calls.
    """

    def start(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> VoiceCallSession:
        """
        Start voice call execution.

        Expected lifecycle:

        READY
          |
          ↓
        ACTIVE
        """

        session = context.session

        if session.state != VoiceCallState.READY:
            raise ValueError(
                "Voice call must be READY "
                "before execution."
            )

        if not context.room.has_character():
            raise ValueError(
                "Voice call room requires "
                "a character participant."
            )

        active_session = VoiceCallSession(
            session_id=session.session_id,
            learner_id=session.learner_id,
            character_id=session.character_id,
            world_id=session.world_id,
            language_code=session.language_code,
            state=VoiceCallState.ACTIVE,
        )

        logger.info(
            "Voice call execution started",
            extra={
                "session_id": active_session.session_id,
                "learner_id": active_session.learner_id,
                "character_id": active_session.character_id,
                "world_id": active_session.world_id,
                "state": active_session.state.value,
            },
        )

        return active_session

    def stop(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> VoiceCallSession:
        """
        Stop voice call execution.

        Expected lifecycle:

        ACTIVE
          |
          ↓
        ENDED
        """

        session = context.session

        if session.state != VoiceCallState.ACTIVE:
            raise ValueError(
                "Only ACTIVE voice calls "
                "can be stopped."
            )

        ended_session = VoiceCallSession(
            session_id=session.session_id,
            learner_id=session.learner_id,
            character_id=session.character_id,
            world_id=session.world_id,
            language_code=session.language_code,
            state=VoiceCallState.ENDED,
        )

        logger.info(
            "Voice call execution ended",
            extra={
                "session_id": ended_session.session_id,
                "learner_id": ended_session.learner_id,
                "character_id": ended_session.character_id,
                "world_id": ended_session.world_id,
                "state": ended_session.state.value,
            },
        )

        return ended_session

    def fail(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> VoiceCallSession:
        """
        Mark execution as failed.
        """

        session = context.session

        failed_session = VoiceCallSession(
            session_id=session.session_id,
            learner_id=session.learner_id,
            character_id=session.character_id,
            world_id=session.world_id,
            language_code=session.language_code,
            state=VoiceCallState.FAILED,
        )

        logger.error(
            "Voice call execution failed",
            extra={
                "session_id": failed_session.session_id,
                "learner_id": failed_session.learner_id,
                "character_id": failed_session.character_id,
                "world_id": failed_session.world_id,
                "state": failed_session.state.value,
            },
        )

        return failed_session

