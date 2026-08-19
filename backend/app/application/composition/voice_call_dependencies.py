"""
Voice Call Shared Dependencies.

Central dependency registry for Beta.

Responsibilities:
- Provide shared repositories.
- Maintain application-level dependencies.

Does NOT:
- Contain business logic.
- Execute workflows.
- Handle HTTP.
"""


from __future__ import annotations



from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)


from app.infrastructure.persistence.in_memory_voice_call_invitation_repository import (
    InMemoryVoiceCallInvitationRepository,
)


from app.infrastructure.persistence.in_memory_voice_call_notification_repository import (
    InMemoryVoiceCallNotificationRepository,
)



#
# Shared Beta repositories.
#
# Future:
# Replace with database implementations.
#

voice_call_repository = (
    InMemoryVoiceCallRepository()
)


voice_call_invitation_repository = (
    InMemoryVoiceCallInvitationRepository()
)


voice_call_notification_repository = (
    InMemoryVoiceCallNotificationRepository()
)



__all__ = [
    "voice_call_repository",
    "voice_call_invitation_repository",
    "voice_call_notification_repository",
]