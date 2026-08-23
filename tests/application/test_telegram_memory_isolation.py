from backend.app.application.conversation.privacy import (
    pseudonymize_identifier,
)


def test_user_ids_are_pseudonymized():
    david = pseudonymize_identifier("1092959244")
    brother = pseudonymize_identifier("9999999999")

    assert david != brother


def test_raw_identifier_is_not_stored():
    value = pseudonymize_identifier("1092959244")

    assert value != "1092959244"
