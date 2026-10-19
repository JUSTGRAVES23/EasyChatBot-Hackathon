
from __future__ import annotations

import logging
import os
from typing import Any

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.application.authorization.authorization_service import PermissionDeniedError
from app.api.dependencies.identity import get_current_principal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequestBody(BaseModel):
    plan_code: str = Field(min_length=1, max_length=100)
    billing_interval: str = Field(min_length=1, max_length=50)


class CheckoutResponse(BaseModel):
    checkout_url: str
    checkout_session_id: str


@router.post("/checkout", response_model=CheckoutResponse)
async def create_billing_checkout(
    body: CheckoutRequestBody,
    request: Request,
    principal: Any = Depends(get_current_principal),  # noqa: B008
) -> CheckoutResponse:
    """Create checkout for the authenticated learner."""

    if not getattr(request.app.state, "paid_checkout_enabled", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Paid checkout is currently unavailable.",
        )

    composition = getattr(request.app.state, "payment_composition", None)
    if composition is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment services are not configured.",
        )

    user_id = getattr(principal, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user identity is unavailable.",
        )

    success_url = os.getenv("EASYWORLD_BILLING_SUCCESS_URL")
    cancel_url = os.getenv("EASYWORLD_BILLING_CANCEL_URL")
    if not success_url or not cancel_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Checkout redirect URLs are not configured.",
        )

    try:
        # CheckoutCreationWorkflow.execute is synchronous.
        session = composition.checkout_creation_workflow.execute(
            user_id=str(user_id),
            plan_code=body.plan_code,
            billing_interval=body.billing_interval,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not permitted to create this checkout.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The requested subscription plan is unavailable.",
        ) from exc
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The payment provider could not create checkout.",
        ) from exc
    except Exception as exc:
        # Log diagnostics server-side; do not expose internal details.
        logger.exception(
            "Unable to complete billing checkout for authenticated user"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Checkout could not be completed.",
        ) from exc

    checkout_url = getattr(session, "checkout_url", None)
    session_id = getattr(session, "provider_session_id", None)

    if not checkout_url or not session_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The payment provider returned an invalid checkout session.",
        )

    return CheckoutResponse(
        checkout_url=checkout_url,
        checkout_session_id=session_id,
    )


@router.post("/webhook/stripe")
async def receive_stripe_webhook(request: Request) -> dict[str, str]:
    """Process verified Stripe events and reconcile World access."""

    composition = getattr(request.app.state, "payment_composition", None)
    if composition is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment services are not configured.",
        )

    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature.",
        )

    payload = await request.body()

    try:
        result = await composition.process_stripe_webhook.execute_async(
            payload=payload,
            signature=signature,
        )
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe signature.",
        ) from exc
    except Exception:
        # Return an error so Stripe can retry failed event processing.
        # Do not expose internal exception details to the caller.
        logger.exception("Stripe webhook processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe event processing failed.",
        ) from None

    return {
        "status": str(result["status"]),
        "event_id": str(result["event_id"]),
    }


__all__ = ["router"]
