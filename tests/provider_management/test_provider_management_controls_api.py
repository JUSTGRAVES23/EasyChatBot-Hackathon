from provider_management.control.provider_delivery_control import ProviderDeliveryControl

def test_provider_control_api_boundary_dependency_exists() -> None:
    assert ProviderDeliveryControl().allow_execution() is True
