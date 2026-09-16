from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.domain.authorization.permissions import Permission
from application.bootstrap import BootstrapGovernance
from src.ai_runtime.capabilities.actor_context import RuntimeActorContext


def _request(*, capability: str, actor=None):
    return SimpleNamespace(capability=capability, actor=actor)


def test_internal_data_read_rejects_missing_actor() -> None:
    decision = BootstrapGovernance().evaluate(
        _request(capability="internal_data_read")
    )

    assert decision.allowed is False


def test_internal_data_read_rejects_beta_user() -> None:
    actor = RuntimeActorContext(
        actor_id="user-1",
        roles=frozenset({"beta_user"}),
    )

    decision = BootstrapGovernance().evaluate(
        _request(
            capability="internal_data_read",
            actor=actor,
        )
    )

    assert decision.allowed is False


@pytest.mark.parametrize("role", ["operator", "admin"])
def test_internal_data_read_allows_authorized_roles(role: str) -> None:
    actor = RuntimeActorContext(
        actor_id="user-1",
        roles=frozenset({role}),
    )

    decision = BootstrapGovernance().evaluate(
        _request(
            capability="internal_data_read",
            actor=actor,
        )
    )

    assert decision.allowed is True


def test_internal_data_read_rejects_unknown_role() -> None:
    actor = RuntimeActorContext(
        actor_id="user-1",
        roles=frozenset({"unknown_role"}),
    )

    decision = BootstrapGovernance().evaluate(
        _request(
            capability="internal_data_read",
            actor=actor,
        )
    )

    assert decision.allowed is False


def test_existing_non_sensitive_capability_remains_allowed() -> None:
    decision = BootstrapGovernance().evaluate(
        _request(capability="live_intelligence")
    )

    assert decision.allowed is True

