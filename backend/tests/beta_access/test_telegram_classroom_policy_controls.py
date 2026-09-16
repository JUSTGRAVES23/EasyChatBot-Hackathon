from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)


@dataclass(frozen=True)
class FakePrincipal:
    user_id: str = "test-user"


class FakeFunctionalityControlService:
    def __init__(self, availability: str = "enabled") -> None:
        self.availability = availability
        self.calls: list[dict[str, Any]] = []

    def get_availability(
        self,
        *,
        environment: str,
        functionality_id: str,
    ) -> str:
        self.calls.append(
            {
                "environment": environment,
                "functionality_id": functionality_id,
            }
        )
        return self.availability


def create_boundary(
    *,
    availability: str = "enabled",
) -> tuple[
    BetaTelegramConversationBoundary,
    FakeFunctionalityControlService,
]:
    control_service = FakeFunctionalityControlService(
        availability=availability,
    )

    conversation_service = MagicMock(name="conversation_service")
    beta_access_service = MagicMock(name="beta_access_service")

    boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation_service,
        beta_access_service=beta_access_service,
        functionality_control_service=control_service,
    )

    return boundary, control_service


def test_enabled_telegram_functionality_is_available() -> None:
    boundary, control_service = create_boundary(
        availability="enabled",
    )

    availability = control_service.get_availability(
        environment="adults",
        functionality_id="telegram",
    )

    assert availability == "enabled"
    assert control_service.calls == [
        {
            "environment": "adults",
            "functionality_id": "telegram",
        }
    ]

    assert boundary._functionality_control_service is control_service


def test_disabled_telegram_functionality_is_available_as_disabled() -> None:
    boundary, control_service = create_boundary(
        availability="disabled",
    )

    availability = control_service.get_availability(
        environment="adults",
        functionality_id="telegram",
    )

    assert availability == "disabled"
    assert control_service.calls == [
        {
            "environment": "adults",
            "functionality_id": "telegram",
        }
    ]

    assert boundary._functionality_control_service is control_service