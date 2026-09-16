"""Explicit registration of the authoritative SQLAlchemy ORM models.

This module exists solely to ensure that the canonical Base.metadata registry
contains the application's authoritative persistence models before consumers
such as schema diagnostics inspect it.

Do not import legacy or duplicate ORM models here.
"""

from app.infrastructure.persistence.beta_access_models import (
    BetaConnectionTokenRecord,
    BetaUserRecord,
    TelegramBindingRecord,
)
from app.infrastructure.persistence.conversation_event_records import (
    ConversationEventRecord,
)
from app.infrastructure.persistence.functionality_control_records import (
    FunctionalityControlAuditRecord,
    FunctionalityControlStateRecord,
)
from app.infrastructure.persistence.learning_world_models import (
    LearningWorldModel,
)
from app.infrastructure.persistence.memory_records import (
    ConversationMemoryRecord,
)
from app.infrastructure.persistence.provider_usage_records import (
    ProviderUsageRecord,
)

__all__ = [
    "BetaConnectionTokenRecord",
    "BetaUserRecord",
    "TelegramBindingRecord",
    "ConversationEventRecord",
    "FunctionalityControlStateRecord",
    "FunctionalityControlAuditRecord",
    "ConversationMemoryRecord",
    "ProviderUsageRecord",
    "LearningWorldModel",
]