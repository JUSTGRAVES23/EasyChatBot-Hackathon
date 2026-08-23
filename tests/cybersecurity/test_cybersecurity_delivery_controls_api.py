from app.api.cybersecurity_delivery_controls import router

def test_cybersecurity_control_router_exists() -> None:
    assert str(router.prefix) == "/controls/cybersecurity"
