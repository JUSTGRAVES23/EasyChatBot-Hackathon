"""SQLAlchemy model for the authoritative Learning World catalogue."""
from __future__ import annotations
from datetime import datetime
from uuid import UUID
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class LearningWorldModel(Base):
    __tablename__ = "learning_worlds"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    identifier: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    language: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    world_type: Mapped[str] = mapped_column(String(50), nullable=False)
    learning_domain: Mapped[str] = mapped_column(String(100), nullable=False)
    runtime_world_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
