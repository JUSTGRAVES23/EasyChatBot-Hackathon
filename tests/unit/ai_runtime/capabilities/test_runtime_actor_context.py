from app.domain.identity.principal import AccountStatus, Principal
from src.ai_runtime.capabilities.actor_context import RuntimeActorContext
from src.ai_runtime.capabilities.models import CapabilityRequest


def principal(role="operator"):
    return Principal(
        user_id="user-1",
        email="user@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({role}),
    )


def test_actor_context_is_runtime_dto_not_principal():
    p = principal()

    actor = RuntimeActorContext(
        actor_id=p.user_id,
        roles=p.roles,
    )

    assert not isinstance(actor, Principal)
    assert actor.actor_id == "user-1"
    assert actor.roles == frozenset({"operator"})
    assert not hasattr(actor, "email")
    assert not hasattr(actor, "account_status")


def test_capability_request_accepts_actor():
    actor = RuntimeActorContext(
        "user-1",
        frozenset({"operator"}),
    )

    request = CapabilityRequest(
        capability="internal_data_read",
        request_id="req-1",
        payload={},
        actor=actor,
    )

    assert request.actor is actor


def test_existing_request_remains_compatible():
    request = CapabilityRequest(
        capability="internal_documentation_search",
        request_id="req-1",
        payload={"query": "test"},
    )

    assert request.actor is None
    assert request.requested_by == "application"

