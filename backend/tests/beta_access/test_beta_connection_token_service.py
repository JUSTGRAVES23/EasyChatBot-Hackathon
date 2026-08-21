from app.application.beta_access.token_service import BetaConnectionTokenService


def test_generated_token_is_hashed():
    raw, hashed = BetaConnectionTokenService.generate()
    assert raw
    assert hashed
    assert raw != hashed
    assert BetaConnectionTokenService.hash_token(raw) == hashed
