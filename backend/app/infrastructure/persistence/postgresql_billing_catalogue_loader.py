"""Load the authoritative billing catalogue from PostgreSQL persistence records.

This adapter deliberately performs no seeding and makes no Stripe API calls.
Unknown persisted enum values fail closed rather than being silently coerced.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.billing.catalogue import (
    BillingCatalogue,
    BillingPlan,
    BillingPrice,
    BillingScope,
    PlanType,
)
from app.infrastructure.persistence.billing_models import (
    BillingPlanRecord,
    BillingPriceRecord,
)


class PostgreSQLBillingCatalogueLoader:
    """Read billing plans/prices and map them into the domain catalogue."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    def load(self) -> BillingCatalogue:
        """Load all configured rows, including inactive rows.

        Inactive records remain represented in the domain catalogue so normal
        domain eligibility checks can reject them. Empty tables yield an empty
        catalogue, which does not make any plan purchasable.
        """
        with self._session_factory() as session:
            plan_rows = session.scalars(
                select(BillingPlanRecord).order_by(BillingPlanRecord.plan_code)
            ).all()
            price_rows = session.scalars(
                select(BillingPriceRecord).order_by(
                    BillingPriceRecord.plan_id,
                    BillingPriceRecord.billing_interval,
                )
            ).all()

            # Convert while the session is open; ORM rows are only read here.
            plans_by_id: dict[object, BillingPlan] = {}
            plans: list[BillingPlan] = []
            for row in plan_rows:
                plan = self._to_plan(row)
                if row.id in plans_by_id:
                    raise ValueError(f"Duplicate billing plan id: {row.id!r}.")
                plans_by_id[row.id] = plan
                plans.append(plan)

            prices: list[BillingPrice] = []
            seen_plan_intervals: set[tuple[str, str]] = set()
            for row in price_rows:
                plan = plans_by_id.get(row.plan_id)
                if plan is None:
                    raise ValueError(
                        "Billing price references an unknown plan_id: "
                        f"{row.plan_id!r}."
                    )
                price = self._to_price(row, plan_code=plan.plan_code)
                key = (price.plan_code, price.billing_interval)
                if key in seen_plan_intervals:
                    raise ValueError(
                        "Duplicate billing price for plan/interval: "
                        f"{key[0]!r}/{key[1]!r}."
                    )
                seen_plan_intervals.add(key)
                prices.append(price)

        return BillingCatalogue(plans=plans, prices=prices)

    @staticmethod
    def _to_plan(row: BillingPlanRecord) -> BillingPlan:
        plan_type_value = _required_string(row.plan_type, "plan_type").lower()
        scope_value = _required_string(row.audience, "audience").lower()

        try:
            plan_type = PlanType(plan_type_value)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported billing plan_type: {row.plan_type!r}."
            ) from exc

        try:
            scope = BillingScope(scope_value)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported billing audience/scope: {row.audience!r}."
            ) from exc

        return BillingPlan(
            plan_code=_required_string(row.plan_code, "plan_code"),
            display_name=_required_string(row.display_name, "display_name"),
            plan_type=plan_type,
            scope=scope,
            family_capable=bool(row.family_capable),
            active=bool(row.active),
        )

    @staticmethod
    def _to_price(
        row: BillingPriceRecord,
        *,
        plan_code: str,
    ) -> BillingPrice:
        interval = _required_string(row.billing_interval, "billing_interval").lower()
        stripe_price_id = _required_string(row.stripe_price_id, "stripe_price_id")
        currency = _required_string(row.currency, "currency").lower()

        if len(currency) != 3 or not currency.isalpha():
            raise ValueError(f"Invalid billing currency: {row.currency!r}.")
        if isinstance(row.amount_minor, bool) or not isinstance(row.amount_minor, int):
            raise ValueError("amount_minor must be an integer.")
        if row.amount_minor < 0:
            raise ValueError("amount_minor cannot be negative.")

        return BillingPrice(
            plan_code=plan_code,
            billing_interval=interval,
            stripe_price_id=stripe_price_id,
            currency=currency,
            amount_minor=row.amount_minor,
            active=bool(row.active),
        )


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


__all__ = ["PostgreSQLBillingCatalogueLoader"]
