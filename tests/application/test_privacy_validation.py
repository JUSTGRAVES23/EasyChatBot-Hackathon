from app.application.privacy.validate import build_beta1_validation_service


def test_beta1_privacy_validation_detects_no_structural_gaps():
    result = build_beta1_validation_service().validate()

    assert result.status == "PASS"
    assert result.checks == 11
    assert result.blocking_failures == 0
    assert result.passed == result.checks

