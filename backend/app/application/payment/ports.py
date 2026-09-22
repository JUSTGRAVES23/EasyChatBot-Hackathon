from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.domain.payment.models import (
    BillingPortalSession,
    CheckoutRequest,
    CheckoutSession,
    PaymentEvent,
)


class PaymentProvider(ABC):
    @abstractmethod
    def create_customer(self, *, user_id: str, email: str, name: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_checkout_session(self, request: CheckoutRequest, *, customer_id: str | None) -> CheckoutSession:
        raise NotImplementedError

    @abstractmethod
    def create_billing_portal_session(self, *, customer_id: str, return_url: str) -> BillingPortalSession:
        raise NotImplementedError

    @abstractmethod
    def construct_webhook_event(self, payload: bytes, signature: str) -> PaymentEvent:
        raise NotImplementedError


class PaymentEventRepository(ABC):
    @abstractmethod
    def has_processed(self, event_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def record_received(self, event: PaymentEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def mark_processed(self, event_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def mark_failed(self, event_id: str, error: str) -> None:
        raise NotImplementedError


class EntitlementService(ABC):
    @abstractmethod
    def handle_payment_event(self, event: PaymentEvent) -> None:
        raise NotImplementedError
