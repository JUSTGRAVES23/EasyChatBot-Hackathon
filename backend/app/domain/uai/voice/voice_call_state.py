"""
Voice Call State.

Domain lifecycle states for
AI character voice calls.

Responsibilities:
- Define valid call lifecycle states.
- Provide explicit state representation.
- Support execution and reconnect lifecycle.

Does NOT:
- Manage LiveKit.
- Manage providers.
- Persist data.
"""

from __future__ import annotations


from enum import Enum



class VoiceCallState(
    str,
    Enum,
):
    """
    Voice call lifecycle states.

    Lifecycle:

        CREATED
            |
            ↓
        PREPARING
            |
            ↓
        READY
            |
            ↓
        ACTIVE
            |
            +----------------+
            |                |
            ↓                |
        DISCONNECTED         |
            |                |
            ↓                |
        RECONNECTABLE -------+
            

        ACTIVE
            |
            ↓
        COMPLETED


    Failure:

        Any state
            |
            ↓
        FAILED
    """


    CREATED = "created"


    PREPARING = "preparing"


    READY = "ready"


    ACTIVE = "active"


    DISCONNECTED = "disconnected"


    RECONNECTABLE = "reconnectable"


    ENDED = "ended"


    COMPLETED = "completed"


    FAILED = "failed"



__all__ = [
    "VoiceCallState",
]