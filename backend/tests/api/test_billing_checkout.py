"""Regression tests for the disabled billing checkout API (M5.5.14-D)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from app.application.authorization.authorization_service import PermissionDeniedError

import stripe
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.billing_checkout import router as billing_checkout_router
from app.api.dependencies.identity import get_current_principal


VALID_CHECKOUT_PAYLOAD = {
    "plan_code": "NORMAL",
    "billing_interval": "monthly",
}


def _build_app(*, authenticated: bool) -> FastAPI:
    """Build an isolated application without database or Stripe startup."""
    app = FastAPI()
    app.state.paid_checkout_enabled = False
    app.state.payment_composition = None

    async def override_principal():
        if not authenticated:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated.",
            )
        return SimpleNamespace(user_id="test-user-001")

    app.dependency_overrides[get_current_principal] = override_principal
    app.include_router(billing_checkout_router)
    return app


def test_checkout_requires_authentication() -> None:
    with TestClient(_build_app(authenticated=False)) as client:
        response = client.post(
            "/billing/checkout",
            json=VALID_CHECKOUT_PAYLOAD,
        )

    assert response.status_code == 401


def test_authenticated_checkout_while_disabled_returns_503() -> None:
    with TestClient(_build_app(authenticated=True)) as client:
        response = client.post(
            "/billing/checkout",
            json=VALID_CHECKOUT_PAYLOAD,
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Paid checkout is currently unavailable."
    )


def test_checkout_without_composition_returns_503() -> None:
    app = _build_app(authenticated=True)
    app.state.paid_checkout_enabled = True
    app.state.payment_composition = None

    with TestClient(app) as client:
        response = client.post(
            "/billing/checkout",
            json=VALID_CHECKOUT_PAYLOAD,
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Payment services are not configured."
    )


def test_webhook_without_composition_returns_503() -> None:
    with TestClient(_build_app(authenticated=False)) as client:
        response = client.post(
            "/billing/webhook/stripe",
            content=b"{}",
            headers={"Stripe-Signature": "t=0,v1=invalid"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Payment services are not configured."
    )


def test_invalid_checkout_payload_returns_422() -> None:
    with TestClient(_build_app(authenticated=True)) as client:
        response = client.post(
            "/billing/checkout",
            json={},
        )

    assert response.status_code == 422


def test_configured_webhook_rejects_missing_signature() -> None:
    execute_async = AsyncMock()

    app = _build_app(authenticated=False)
    app.state.payment_composition = SimpleNamespace(
        process_stripe_webhook=SimpleNamespace(
            execute_async=execute_async
        )
    )

    with TestClient(app) as client:
        response = client.post(
            "/billing/webhook/stripe",
            content=b"{}",
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Missing Stripe signature."
    execute_async.assert_not_awaited()


def test_configured_webhook_rejects_invalid_signature() -> None:
    execute_async = AsyncMock(
        side_effect=stripe.error.SignatureVerificationError(
            "Invalid signature",
            "t=0,v1=invalid",
        )
    )

    app = _build_app(authenticated=False)
    app.state.payment_composition = SimpleNamespace(
        process_stripe_webhook=SimpleNamespace(
            execute_async=execute_async
        )
    )

    with TestClient(app) as client:
        response = client.post(
            "/billing/webhook/stripe",
            content=b"{}",
            headers={
                "content-type": "application/json",
                "Stripe-Signature": "t=0,v1=invalid",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Stripe signature."
    execute_async.assert_awaited_once()


def test_unexpected_checkout_failure_returns_safe_500(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "EASYWORLD_BILLING_SUCCESS_URL",
        "https://easyworld.test/success",
    )
    monkeypatch.setenv(
        "EASYWORLD_BILLING_CANCEL_URL",
        "https://easyworld.test/cancel",
    )

    app = _build_app(authenticated=True)
    app.state.paid_checkout_enabled = True

    execute = Mock(
        side_effect=RuntimeError("internal database details")
    )
    app.state.payment_composition = SimpleNamespace(
        checkout_creation_workflow=SimpleNamespace(
            execute=execute
        )
    )

    with TestClient(app) as client:
        response = client.post(
            "/billing/checkout",
            json=VALID_CHECKOUT_PAYLOAD,
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Checkout could not be completed."
    assert "internal database details" not in response.text
    execute.assert_called_once()

def test_permission_denial_returns_403(monkeypatch) -> None:

    monkeypatch.setenv("EASYWORLD_BILLING_SUCCESS_URL", "https://easyworld.test/success")
    monkeypatch.setenv("EASYWORLD_BILLING_CANCEL_URL", "https://easyworld.test/cancel")

    app = _build_app(authenticated=True)
    app.state.paid_checkout_enabled = True
    execute = Mock(
        side_effect=PermissionDeniedError("Permission required: billing.checkout.")
    )
    app.state.payment_composition = SimpleNamespace(
        checkout_creation_workflow=SimpleNamespace(execute=execute)
    )

    with TestClient(app) as client:
        response = client.post("/billing/checkout", json=VALID_CHECKOUT_PAYLOAD)

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not permitted to create this checkout."
    assert "billing.checkout" not in response.text
    execute.assert_called_once()
def test_successful_checkout_returns_session_details(monkeypatch) -> None:
    monkeypatch.setenv(
        "EASYWORLD_BILLING_SUCCESS_URL",
        "https://easyworld.test/success",
    )
    monkeypatch.setenv(
        "EASYWORLD_BILLING_CANCEL_URL",
        "https://easyworld.test/cancel",
    )

    app = _build_app(authenticated=True)
    app.state.paid_checkout_enabled = True

    execute = Mock(
        return_value=SimpleNamespace(
            checkout_url="https://checkout.stripe.test/session",
            provider_session_id="cs_test_example",
        )
    )
    app.state.payment_composition = SimpleNamespace(
        checkout_creation_workflow=SimpleNamespace(execute=execute)
    )

    with TestClient(app) as client:
        response = client.post(
            "/billing/checkout",
            json=VALID_CHECKOUT_PAYLOAD,
        )

    assert response.status_code == 200
    assert response.json() == {
        "checkout_url": "https://checkout.stripe.test/session",
        "checkout_session_id": "cs_test_example",
    }
    execute.assert_called_once_with(
        user_id="test-user-001",
        plan_code="NORMAL",
        billing_interval="monthly",
        success_url="https://easyworld.test/success",
        cancel_url="https://easyworld.test/cancel",
    )


def test_checkout_without_redirect_urls_returns_503(monkeypatch) -> None:
    monkeypatch.delenv("EASYWORLD_BILLING_SUCCESS_URL", raising=False)
    monkeypatch.delenv("EASYWORLD_BILLING_CANCEL_URL", raising=False)

    app = _build_app(authenticated=True)
    app.state.paid_checkout_enabled = True
    execute = Mock()
    app.state.payment_composition = SimpleNamespace(
        checkout_creation_workflow=SimpleNamespace(execute=execute)
    )

    with TestClient(app) as client:
        response = client.post(
            "/billing/checkout",
            json=VALID_CHECKOUT_PAYLOAD,
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Checkout redirect URLs are not configured."
    )
    execute.assert_not_called()


def test_stripe_checkout_failure_returns_502(monkeypatch) -> None:
    monkeypatch.setenv(
        "EASYWORLD_BILLING_SUCCESS_URL",
        "https://easyworld.test/success",
    )
    monkeypatch.setenv(
        "EASYWORLD_BILLING_CANCEL_URL",
        "https://easyworld.test/cancel",
    )

    app = _build_app(authenticated=True)
    app.state.paid_checkout_enabled = True
    execute = Mock(
        side_effect=stripe.error.StripeError("simulated provider failure")
    )
    app.state.payment_composition = SimpleNamespace(
        checkout_creation_workflow=SimpleNamespace(execute=execute)
    )

    with TestClient(app) as client:
        response = client.post(
            "/billing/checkout",
            json=VALID_CHECKOUT_PAYLOAD,
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "The payment provider could not create checkout."
    )
    assert "simulated provider failure" not in response.text
    execute.assert_called_once()


def test_invalid_provider_checkout_session_returns_502(monkeypatch) -> None:
    monkeypatch.setenv(
        "EASYWORLD_BILLING_SUCCESS_URL",
        "https://easyworld.test/success",
    )
    monkeypatch.setenv(
        "EASYWORLD_BILLING_CANCEL_URL",
        "https://easyworld.test/cancel",
    )

    app = _build_app(authenticated=True)
    app.state.paid_checkout_enabled = True
    execute = Mock(
        return_value=SimpleNamespace(
            checkout_url=None,
            provider_session_id="cs_test_example",
        )
    )
    app.state.payment_composition = SimpleNamespace(
        checkout_creation_workflow=SimpleNamespace(execute=execute)
    )

    with TestClient(app) as client:
        response = client.post(
            "/billing/checkout",
            json=VALID_CHECKOUT_PAYLOAD,
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "The payment provider returned an invalid checkout session."
    )
    execute.assert_called_once()
