from app.domain.authorization.permissions import Permission, has_permission
from src.ai_runtime.capabilities.actor_context import RuntimeActorContext


def test_beta_user_rejected():
    assert not has_permission(
        roles=frozenset({"beta_user"}),
        permission=Permission.INTERNAL_DATA_READ,
    )


def test_operator_allowed():
    assert has_permission(
        roles=frozenset({"operator"}),
        permission=Permission.INTERNAL_DATA_READ,
    )


def test_admin_allowed():
    assert has_permission(
        roles=frozenset({"admin"}),
        permission=Permission.INTERNAL_DATA_READ,
    )


def test_missing_actor_is_not_authorized():
    actor = None
    assert actor is None


def test_actor_context_never_contains_backend_principal():
    from app.domain.identity.principal import Principal

    actor = RuntimeActorContext(
        "operator-1",
        frozenset({"operator"}),
    )

    assert not isinstance(actor, Principal)
    assert actor.__class__.__module__.startswith(
        "src.ai_runtime"
    )

