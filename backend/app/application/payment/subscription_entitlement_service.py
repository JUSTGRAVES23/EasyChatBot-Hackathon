from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.payment.models import PaymentEvent


@dataclass(frozen=True, slots=True)
class SubscriptionEntitlementResult:
    """Authoritative result of applying a subscription entitlement event."""

    beneficiary_user_id: str
    plan_code: str
    active: bool


class SubscriptionEntitlementService:
    """Apply verified Stripe subscription events to EASYWORLD persistence.

    Stripe is the payment system of record.
    EASYWORLD subscription and entitlement persistence is the access system
    of record.

    This service deliberately contains no Stripe SDK calls.

    The service remains synchronous. World-access reconciliation is performed
    by the separate SubscriptionEntitlementWorldAccessOrchestrator boundary.
    """

    SUBSCRIPTION_EVENTS = {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }

    def __init__(
        self,
        subscription_repository,
        entitlement_repository,
    ) -> None:
        if subscription_repository is None:
            raise ValueError("subscription_repository cannot be None.")

        if entitlement_repository is None:
            raise ValueError("entitlement_repository cannot be None.")

        self.subscription_repository = subscription_repository
        self.entitlement_repository = entitlement_repository

    def handle_payment_event(
        self,
        event: PaymentEvent,
    ) -> SubscriptionEntitlementResult | None:
        """Apply a subscription event and return its authoritative state.

        Non-subscription payment events remain ignored and return ``None``.

        The returned result contains only the persisted entitlement state
        required by the next application boundary. It does not perform
        World-access authorization or invoke asynchronous services.
        """
        if not isinstance(event, PaymentEvent):
            raise TypeError("event must be a PaymentEvent.")

        if event.event_type not in self.SUBSCRIPTION_EVENTS:
            return None

        subscription = self._extract_subscription(event)

        beneficiary_user_id = self._metadata_value(
            subscription,
            "easyworld_user_id",
        )

        if not beneficiary_user_id:
            raise ValueError(
                "Stripe subscription is missing easyworld_user_id metadata."
            )

        payer_user_id = self._metadata_value(
            subscription,
            "easyworld_payer_user_id",
        ) or beneficiary_user_id

        plan_code = self._metadata_value(
            subscription,
            "easyworld_plan_code",
        )

        if not plan_code:
            raise ValueError(
                "Stripe subscription is missing easyworld_plan_code metadata."
            )

        stripe_subscription_id = subscription.get("id")
        stripe_customer_id = self._customer_id(
            subscription.get("customer")
        )
        stripe_price_id = self._price_id(subscription)

        if not stripe_subscription_id:
            raise ValueError("Stripe subscription is missing id.")

        if not stripe_customer_id:
            raise ValueError("Stripe subscription is missing customer.")

        if not stripe_price_id:
            raise ValueError("Stripe subscription is missing price.")

        status = str(subscription.get("status") or "unknown")

        current_period_start = self._timestamp(
            subscription.get("current_period_start")
        )
        current_period_end = self._timestamp(
            subscription.get("current_period_end")
        )

        cancel_at_period_end = bool(
            subscription.get("cancel_at_period_end", False)
        )

        self.subscription_repository.upsert(
            beneficiary_user_id=beneficiary_user_id,
            payer_user_id=payer_user_id,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_price_id=stripe_price_id,
            plan_code=plan_code,
            status=status,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
        )

        active = status in {
            "trialing",
            "active",
        }

        self.entitlement_repository.upsert(
            user_id=beneficiary_user_id,
            plan_code=plan_code,
            active=active,
        )

        return SubscriptionEntitlementResult(
            beneficiary_user_id=beneficiary_user_id,
            plan_code=plan_code,
            active=active,
        )

    @staticmethod
    def _extract_subscription(
        event: PaymentEvent,
    ) -> dict[str, Any]:
        data = event.payload.get("data")

        if not isinstance(data, dict):
            raise ValueError("Stripe event is missing data.")

        obj = data.get("object")

        if not isinstance(obj, dict):
            raise ValueError("Stripe event is missing subscription object.")

        return obj

    @staticmethod
    def _metadata_value(
        subscription: dict[str, Any],
        key: str,
    ) -> str | None:
        metadata = subscription.get("metadata")

        if not isinstance(metadata, dict):
            return None

        value = metadata.get(key)

        if value is None:
            return None

        value = str(value).strip()

        return value or None

    @staticmethod
    def _customer_id(customer: Any) -> str | None:
        if isinstance(customer, str):
            return customer

        if isinstance(customer, dict):
            value = customer.get("id")
            return str(value) if value else None

        return None

    @staticmethod
    def _price_id(
        subscription: dict[str, Any],
    ) -> str | None:
        items = subscription.get("items")

        if not isinstance(items, dict):
            return None

        data = items.get("data")

        if not isinstance(data, list) or not data:
            return None

        first_item = data[0]

        if not isinstance(first_item, dict):
            return None

        price = first_item.get("price")

        if isinstance(price, str):
            return price

        if isinstance(price, dict):
            value = price.get("id")
            return str(value) if value else None

        return None

    @staticmethod
    def _timestamp(value: Any) -> datetime | None:
        if value is None:
            return None

        try:
            return datetime.fromtimestamp(float(value))
        except (TypeError, ValueError, OSError) as exc:
            raise ValueError(
                f"Invalid Stripe timestamp: {value!r}."
            ) from exc


__all__ = [
    "SubscriptionEntitlementResult",
    "SubscriptionEntitlementService",
]