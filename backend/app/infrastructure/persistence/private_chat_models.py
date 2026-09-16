from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


class PrivateChatConversationRecord(Base):
    """Durable ownership boundary for an authenticated private chat."""

    __tablename__ = "private_chat_conversations"

    conversation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    world_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    messages: Mapped[list["PrivateChatMessageRecord"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PrivateChatMessageRecord.created_at",
    )

    active_conversation: Mapped["PrivateChatActiveConversationRecord | None"] = (
        relationship(
            back_populates="conversation",
            uselist=False,
            passive_deletes=True,
        )
    )

    __table_args__ = (
        Index(
            "ix_private_chat_conversations_user_world",
            "user_id",
            "world_id",
        ),
    )


class PrivateChatMessageRecord(Base):
    """A message belonging to one owned private-chat conversation."""

    __tablename__ = "private_chat_messages"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    conversation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "private_chat_conversations.conversation_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    world_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    conversation: Mapped[PrivateChatConversationRecord] = relationship(
        back_populates="messages",
    )

    __table_args__ = (
        Index(
            "ix_private_chat_messages_conversation_created",
            "conversation_id",
            "created_at",
        ),
        Index(
            "ix_private_chat_messages_user_conversation",
            "user_id",
            "conversation_id",
        ),
    )


class PrivateChatActiveConversationRecord(Base):
    """Server-owned pointer to the active conversation for one user and World.

    Historical conversations are never overwritten or deleted when a new
    conversation is started. This table contains only the current active
    pointer for each user/World pair.
    """

    __tablename__ = "private_chat_active_conversations"

    user_id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    world_id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    conversation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "private_chat_conversations.conversation_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    conversation: Mapped[PrivateChatConversationRecord] = relationship(
        back_populates="active_conversation",
    )

    __table_args__ = (
        Index(
            "ix_private_chat_active_conversations_conversation",
            "conversation_id",
        ),
    )