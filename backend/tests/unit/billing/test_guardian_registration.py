from app.application.payment.guardian_registration import (
    RegistrationPolicyClassification,
    evaluate_guardian_registration_requirement,
)


def test_minor_can_require_guardian_without_hard_coded_age_threshold():
    result = evaluate_guardian_registration_requirement(
        RegistrationPolicyClassification.MINOR,
        guardian_required=True,
    )

    assert result.guardian_required is True
    assert result.required is True
    assert result.guardian_email is None
    assert (
        result.policy_classification
        == RegistrationPolicyClassification.MINOR
    )


def test_guardian_email_is_normalized_when_guardian_required():
    result = evaluate_guardian_registration_requirement(
        RegistrationPolicyClassification.MINOR,
        " Parent@Example.COM ",
        guardian_required=True,
    )

    assert result.guardian_required is True
    assert result.guardian_email == "parent@example.com"


def test_adult_does_not_require_guardian_by_default():
    result = evaluate_guardian_registration_requirement(
        RegistrationPolicyClassification.ADULT,
    )

    assert result.guardian_required is False
    assert result.required is False
    assert result.guardian_email is None


def test_student_does_not_automatically_require_guardian():
    result = evaluate_guardian_registration_requirement(
        RegistrationPolicyClassification.STUDENT,
    )

    assert result.guardian_required is False
    assert result.guardian_email is None


def test_minor_does_not_automatically_mean_guardian_required():
    result = evaluate_guardian_registration_requirement(
        RegistrationPolicyClassification.MINOR,
    )

    assert result.guardian_required is False
    assert result.guardian_email is None


def test_guardian_email_is_not_retained_when_guardian_not_required():
    result = evaluate_guardian_registration_requirement(
        RegistrationPolicyClassification.ADULT,
        " Parent@Example.COM ",
        guardian_required=False,
    )

    assert result.guardian_required is False
    assert result.guardian_email is None