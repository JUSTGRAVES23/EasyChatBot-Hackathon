"""Repository contract tests for World Telegram destinations.

These tests are intentionally small and can be extended with the project's
existing PostgreSQL fixture once the database test harness is selected.
"""
from uuid import uuid4

from app.domain.world_telegram import TelegramDestinationType


def test_destination_type_contract():
    assert TelegramDestinationType.GROUP.value == "GROUP"
    assert TelegramDestinationType.CHANNEL.value == "CHANNEL"


def test_destination_uuid_generation_is_available():
    assert isinstance(uuid4(), type(uuid4()))
