import pytest

from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)


class Authorizer:
    def __init__(self, allowed=True):
        self.allowed = allowed

    def can_control_functionality(self, *, actor, environment, functionality_id):
        return self.allowed


class Auditor:
    def __init__(self):
        self.events = []

    def record_functionality_control(self, **event):
        self.events.append(event)


def make_service(allowed=True):
    auditor = Auditor()
    return FunctionalityOperationalControlService(
        authorizer=Authorizer(allowed), auditor=auditor
    ), auditor


def test_stop_requires_reason():
    service, _ = make_service()
    with pytest.raises(ValueError, match="reason is required"):
        service.stop(actor="operator", actor_name="operator",
                     environment="adults", functionality_id="conversation",
                     reason="   ")


def test_stop_disables_and_audits():
    service, auditor = make_service()
    result = service.stop(actor="operator", actor_name="operator",
                          environment="kids", functionality_id="conversation",
                          reason="Provider incident")
    assert result.availability == "disabled"
    assert service.get_availability(
        environment="kids", functionality_id="conversation"
    ) == "disabled"
    assert len(auditor.events) == 1
    assert auditor.events[0]["action"] == "stop"
    assert auditor.events[0]["reason"] == "Provider incident"


def test_resume_enables_and_audits():
    service, auditor = make_service()
    service.stop(actor="operator", actor_name="operator",
                 environment="adults", functionality_id="conversation",
                 reason="Temporary issue")
    result = service.resume(actor="operator", actor_name="operator",
                            environment="adults", functionality_id="conversation")
    assert result.availability == "enabled"
    assert service.get_availability(
        environment="adults", functionality_id="conversation"
    ) == "enabled"
    assert [e["action"] for e in auditor.events] == ["stop", "resume"]


def test_authorisation_is_enforced():
    service, _ = make_service(False)
    with pytest.raises(PermissionError):
        service.stop(actor="operator", actor_name="operator",
                     environment="adults", functionality_id="conversation",
                     reason="Temporary issue")


@pytest.mark.parametrize("environment", ["invalid", "", "KIDS"])
def test_environment_is_strict(environment):
    service, _ = make_service()
    with pytest.raises(ValueError):
        service.resume(actor="operator", actor_name="operator",
                       environment=environment, functionality_id="conversation")


def test_unknown_functionality_is_rejected():
    service, _ = make_service()
    with pytest.raises(ValueError, match="Unknown functionality_id"):
        service.resume(
            actor="operator",
            actor_name="operator",
            environment="adults",
            functionality_id="arbitrary-production-control",
        )


def test_known_functionality_is_accepted():
    service, _ = make_service()
    result = service.resume(
        actor="operator",
        actor_name="operator",
        environment="adults",
        functionality_id="conversation",
    )
    assert result.functionality_id == "conversation"
    assert result.availability == "enabled"


class Repository:
    def __init__(self):
        self.availability = {}
        self.last_actions = {}
        self.transitions = []

    def get_availability(self, *, environment, functionality_id):
        return self.availability.get((environment, functionality_id), "enabled")

    def get_last_action(self, *, environment, functionality_id):
        return self.last_actions.get((environment, functionality_id))

    def record_transition(self, **kwargs):
        from app.application.provider_management.functionality_operational_control_service import (
            OperationalControlResult,
        )

        self.transitions.append(kwargs)

        result = OperationalControlResult(
            functionality_id=kwargs["functionality_id"],
            environment=kwargs["environment"],
            availability=kwargs["availability"],
            action=kwargs["action"],
            reason=kwargs["reason"],
            changed_at=kwargs["changed_at"],
            changed_by=kwargs["changed_by"],
        )

        key = (result.environment, result.functionality_id)
        self.availability[key] = result.availability
        self.last_actions[key] = result
        return result


def test_repository_path_persists_stop_transition():
    from app.application.provider_management.functionality_operational_control_service import (
        FunctionalityOperationalControlService,
    )

    repository = Repository()
    service = FunctionalityOperationalControlService(
        authorizer=Authorizer(),
        repository=repository,
    )

    result = service.stop(
        actor="operator",
        actor_name="operator",
        environment="kids",
        functionality_id="conversation",
        reason="Provider incident",
    )

    assert result.availability == "disabled"
    assert repository.transitions[0]["action"] == "stop"
    assert service.get_availability(
        environment="kids",
        functionality_id="conversation",
    ) == "disabled"


def test_repository_path_persists_resume_transition():
    from app.application.provider_management.functionality_operational_control_service import (
        FunctionalityOperationalControlService,
    )

    repository = Repository()
    service = FunctionalityOperationalControlService(
        authorizer=Authorizer(),
        repository=repository,
    )

    result = service.resume(
        actor="operator",
        actor_name="operator",
        environment="adults",
        functionality_id="telegram",
    )

    assert result.availability == "enabled"
    assert repository.transitions[0]["action"] == "resume"

