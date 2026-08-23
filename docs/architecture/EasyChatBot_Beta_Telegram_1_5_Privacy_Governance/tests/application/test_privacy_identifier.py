from backend.app.application.privacy.privacy_identifier_service import (
    PrivacyIdentifierService,
)


def test_same_identifier_same_hash():
    service = PrivacyIdentifierService(secret="test-secret")
    assert service.pseudonymize_identifier("1092959244") == service.pseudonymize_identifier("1092959244")


def test_different_identifiers_different_hash():
    service = PrivacyIdentifierService(secret="test-secret")
    assert service.pseudonymize_identifier("a") != service.pseudonymize_identifier("b")
