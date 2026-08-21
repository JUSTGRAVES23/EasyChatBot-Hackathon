from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session


class Base(DeclarativeBase):
    pass


def database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError(
            "DATABASE_URL is required for Beta Telegram persistence."
        )
    return value


def create_database_engine():
    return create_engine(
        database_url(),
        pool_pre_ping=True,
        future=True,
    )


def create_session_factory(engine):
    return sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )
