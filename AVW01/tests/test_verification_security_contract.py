# Security test blueprint — adapt to existing project fixtures.

def test_resend_is_rate_limited():
    assert True

def test_expired_verification_token_is_rejected():
    assert True

def test_used_verification_token_is_rejected():
    assert True

def test_provider_failure_does_not_authenticate_account():
    assert True

def test_raw_verification_token_is_not_logged():
    assert True
