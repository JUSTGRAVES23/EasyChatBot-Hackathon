from datetime import datetime, timezone

from app.infrastructure.persistence.postgresql_parent_child_relationship_repository import (
    PostgreSQLParentChildRelationshipRepository,
)
from app.infrastructure.persistence.postgresql_parental_consent_repository import (
    PostgreSQLParentalConsentRepository,
)


class FakeSessionFactory:
    pass


def test_relationship_repository_requires_session_factory():
    try:
        PostgreSQLParentChildRelationshipRepository(None)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_consent_repository_requires_session_factory():
    try:
        PostgreSQLParentalConsentRepository(None)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_consent_type_is_paid_subscription():
    assert (
        PostgreSQLParentalConsentRepository.PAYMENT_CONSENT_TYPE
        == "PAID_SUBSCRIPTION"
    )


def test_relationship_repository_module_imports():
    assert PostgreSQLParentChildRelationshipRepository is not None


def test_consent_repository_module_imports():
    assert PostgreSQLParentalConsentRepository is not None
