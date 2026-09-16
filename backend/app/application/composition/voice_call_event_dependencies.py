"""
Voice Call Event Dependencies.

Shared application dependencies
for voice lifecycle events.

Does NOT:
- Contain business logic.
- Execute workflows.
- Handle HTTP.
"""

from __future__ import annotations


from app.infrastructure.persistence.in_memory_voice_call_event_repository import (
    InMemoryVoiceCallEventRepository,
)



#
# Beta repository.
#
# Future:
# Replace with PostgreSQL implementation.
#

voice_call_event_repository = (
    InMemoryVoiceCallEventRepository()
)



__all__ = [
    "voice_call_event_repository",
]

