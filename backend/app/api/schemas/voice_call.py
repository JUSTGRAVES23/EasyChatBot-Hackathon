"""
Voice Call API Schemas.

Stable HTTP contracts for
frontend communication.

Does NOT:
- Contain business logic.
- Execute services.
- Access persistence.
"""

from __future__ import annotations


from pydantic import BaseModel



class VoiceCallTriggerRequestSchema(
    BaseModel,
):
    """
    Request to trigger voice workflow.
    """

    learner_id: str

    character_id: str

    world_id: str

    language_code: str

    channel: str



class VoiceCallTriggerResponseSchema(
    BaseModel,
):
    """
    Response after triggering voice call.
    """

    voice_call_id: str

    invitation_id: str

    notification_id: str



class VoiceCallAcceptanceResponseSchema(
    BaseModel,
):
    """
    Response after accepting voice call.
    """

    voice_call_id: str

    learner_id: str

    character_id: str

    session_id: str

    state: str



class VoiceReconnectResponseSchema(
    BaseModel,
):
    """
    Response for reconnecting voice call.

    Returns restored voice identity
    and session information.
    """

    voice_call_id: str

    #
    # Optional for backward compatibility
    # with existing API clients/tests.
    #
    character_id: str | None = None

    language_code: str | None = None

    session_id: str

    state: str



__all__ = [
    "VoiceCallTriggerRequestSchema",
    "VoiceCallTriggerResponseSchema",
    "VoiceCallAcceptanceResponseSchema",
    "VoiceReconnectResponseSchema",
]