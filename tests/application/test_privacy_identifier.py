from __future__ import annotations


import pytest


from backend.app.application.privacy.privacy_identifier_service import (
    PrivacyIdentifierService,
)



def test_same_identifier_generates_same_hash():

    service = PrivacyIdentifierService(
        secret="test-secret",
    )


    first = (
        service.pseudonymize_identifier(
            "1092959244"
        )
    )


    second = (
        service.pseudonymize_identifier(
            "1092959244"
        )
    )


    assert first == second



def test_different_identifiers_generate_different_hashes():

    service = PrivacyIdentifierService(
        secret="test-secret",
    )


    david = (
        service.pseudonymize_identifier(
            "1092959244"
        )
    )


    brother = (
        service.pseudonymize_identifier(
            "2222222222"
        )
    )


    assert david != brother



def test_hash_does_not_contain_original_identifier():

    service = PrivacyIdentifierService(
        secret="test-secret",
    )


    result = (
        service.pseudonymize_identifier(
            "1092959244"
        )
    )


    assert "1092959244" not in result



def test_empty_identifier_rejected():

    service = PrivacyIdentifierService(
        secret="test-secret",
    )


    with pytest.raises(ValueError):

        service.pseudonymize_identifier("")