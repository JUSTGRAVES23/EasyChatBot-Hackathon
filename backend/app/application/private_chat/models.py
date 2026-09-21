"""Application models for authenticated World private chat.

These models define the application-layer contracts used by the
PrivateChatService and its repository. They intentionally contain no
infrastructure or provider-specific behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class LearningWorldCatalogueEntry:
    """Application representation of an authoritative Learning World."""

    id: UUID
    identifier: str
    name: str
    description: str
    language: str
    version: str
    status: str
    enabled: bool
    world_type: str
    learning_domain: str
    runtime_world_id: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("Learning World catalogue id must be a UUID.")

        for field_name in (
            "identifier",
            "name",
            "version",
            "status",
            "world_type",
            "learning_domain",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Learning World catalogue {field_name} cannot be empty."
                )

        if not isinstance(self.description, str):
            raise ValueError(
                "Learning World catalogue description must be a string."
            )

        if not isinstance(self.language, str) or not self.language.strip():
            raise ValueError(
                "Learning World catalogue language cannot be empty."
            )

        if self.runtime_world_id is not None:
            if (
                not isinstance(self.runtime_world_id, str)
                or not self.runtime_world_id.strip()
            ):
                raise ValueError(
                    "runtime_world_id cannot be blank when provided."
                )


@dataclass(frozen=True, slots=True)
class PrivateChatConversation:
    """Application representation of a private chat conversation."""

    conversation_id: UUID
    user_id: str
    world_id: str
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.conversation_id, UUID):
            raise ValueError("conversation_id must be a UUID.")

        if not isinstance(self.user_id, str) or not self.user_id.strip():
            raise ValueError("user_id cannot be empty.")

        if not isinstance(self.world_id, str) or not self.world_id.strip():
            raise ValueError("world_id cannot be empty.")

        if not isinstance(self.created_at, datetime):
            raise ValueError("created_at must be a datetime.")

        if not isinstance(self.updated_at, datetime):
            raise ValueError("updated_at must be a datetime.")


@dataclass(frozen=True, slots=True)
class PrivateChatMessage:
    """Application representation of a private chat message."""

    conversation_id: UUID
    role: str
    content: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.conversation_id, UUID):
            raise ValueError("conversation_id must be a UUID.")

        if not isinstance(self.role, str) or not self.role.strip():
            raise ValueError("role cannot be empty.")

        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("content cannot be empty.")

        if not isinstance(self.created_at, datetime):
            raise ValueError("created_at must be a datetime.")


@dataclass(frozen=True, slots=True)
class PrivateChatActiveConversation:
    """Application representation of the active private chat state."""

    conversation: PrivateChatConversation
    messages: list[PrivateChatMessage]

    def __post_init__(self) -> None:
        if not isinstance(self.conversation, PrivateChatConversation):
            raise ValueError(
                "conversation must be a PrivateChatConversation."
            )

        if not isinstance(self.messages, list):
            raise ValueError("messages must be a list.")

        if not all(
            isinstance(message, PrivateChatMessage)
            for message in self.messages
        ):
            raise ValueError(
                "messages must contain only PrivateChatMessage instances."
            )


@dataclass(frozen=True, slots=True)
class PrivateChatResponse:
    """Application response returned after processing a private chat message."""

    conversation: PrivateChatConversation
    user_message: PrivateChatMessage
    assistant_message: PrivateChatMessage
    response_language: str

    def __post_init__(self) -> None:
        if not isinstance(self.conversation, PrivateChatConversation):
            raise ValueError(
                "conversation must be a PrivateChatConversation."
            )

        if not isinstance(self.user_message, PrivateChatMessage):
            raise ValueError(
                "user_message must be a PrivateChatMessage."
            )

        if not isinstance(self.assistant_message, PrivateChatMessage):
            raise ValueError(
                "assistant_message must be a PrivateChatMessage."
            )

        if (
            not isinstance(self.response_language, str)
            or not self.response_language.strip()
        ):
            raise ValueError("response_language cannot be empty.")