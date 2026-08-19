"""
Voice Call Notification Composition.

Composition root for voice call
notification application services.

Responsibilities:
- Build notification dependencies.
- Wire repository implementation.
- Return configured application service.

Does NOT:
- Handle HTTP.
- Send emails.
- Send push notifications.
- Manage inbox UI.
- Execute voice calls.
"""

from __future__ import annotations



from app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)


from app.infrastructure.persistence.in_memory_voice_call_notification_repository import (
    InMemoryVoiceCallNotificationRepository,
)



#
# Application lifetime repository.
#
# Temporary Beta implementation.
#
# Future replacement:
#
# PostgreSQLVoiceCallNotificationRepository
#
# without changing application services.
#

_voice_call_notification_repository = (
    InMemoryVoiceCallNotificationRepository()
)



def create_voice_call_notification_service(
) -> VoiceCallNotificationService:
    """
    Create configured notification service.
    """


    return VoiceCallNotificationService(
        repository=(
            _voice_call_notification_repository
        ),
    )



def build_voice_call_notification_service(
) -> VoiceCallNotificationService:
    """
    Dependency builder.

    Used by API/application adapters.
    """


    return (
        create_voice_call_notification_service()
    )



__all__ = [
    "create_voice_call_notification_service",
    "build_voice_call_notification_service",
]