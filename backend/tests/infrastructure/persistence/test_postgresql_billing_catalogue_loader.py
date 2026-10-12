"""Focused tests for PostgreSQLBillingCatalogueLoader."""
from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.domain.billing.catalogue import BillingScope, PlanType
from app.infrastructure.persistence.postgresql_billing_catalogue_loader import (
    PostgreSQLBillingCatalogueLoader,
)


class FakeScalarResult:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return self._rows


class FakeSession:
    def __init__(self, plan_rows=(), price_rows=()):
        self._results = [FakeScalarResult(plan_rows), FakeScalarResult(price_rows)]
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def scalars(self, statement):
        self.statements.append(statement)
        return self._results[len(self.statements) - 1]


class FakeSessionFactory:
    def __init__(self, session):
        self.session = session

    def __call__(self):
        return self.session


def plan_row(**overrides):
    values = dict(
        id=uuid4(),
        plan_code="PREMIUM",
        display_name="Premium",
        plan_type="premium",
        audience="individual",
        family_capable=False,
        active=True,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def price_row(plan_id, **overrides):
    values = dict(
        id=uuid4(),
        plan_id=plan_id,
        billing_interval="month",
        stripe_price_id="price_test_authoritative_placeholder",
        currency="EUR",
        amount_minor=1999,
        active=True,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def loader_for(session):
    return PostgreSQLBillingCatalogueLoader(FakeSessionFactory(session))


def test_load_maps_plan_and_price_fields():
    plan = plan_row()
    session = FakeSession([plan], [price_row(plan.id)])

    catalogue = loader_for(session).load()

    loaded_plan = catalogue.get_plan("PREMIUM")
    loaded_price = catalogue.get_price(
        plan_code="PREMIUM",
        billing_interval="month",
    )
    assert loaded_plan.plan_type is PlanType.PREMIUM
    assert loaded_plan.scope is BillingScope.INDIVIDUAL
    assert loaded_price.plan_code == "PREMIUM"
    assert loaded_price.currency == "eur"
    assert loaded_price.amount_minor == 1999
    assert len(session.statements) == 2


def test_empty_tables_load_empty_catalogue_and_do_not_enable_plans():
    catalogue = loader_for(FakeSession()).load()

    with pytest.raises(ValueError, match="Unknown billing plan"):
        catalogue.get_plan("PREMIUM")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("plan_type", "enterprise", "Unsupported billing plan_type"),
        ("audience", None, "audience must be a non-empty string"),
        ("audience", "public", "Unsupported billing audience/scope"),
    ],
)
def test_invalid_plan_mapping_fails_closed(field, value, message):
    plan = plan_row(**{field: value})

    with pytest.raises(ValueError, match=message):
        loader_for(FakeSession([plan], [])).load()


def test_price_with_unknown_plan_id_fails_closed():
    known_plan = plan_row()
    price = price_row(uuid4())

    with pytest.raises(ValueError, match="unknown plan_id"):
        loader_for(FakeSession([known_plan], [price])).load()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("currency", "EURO", "Invalid billing currency"),
        ("amount_minor", -1, "amount_minor cannot be negative"),
        ("stripe_price_id", " ", "stripe_price_id must be a non-empty string"),
    ],
)
def test_invalid_price_data_fails_closed(field, value, message):
    plan = plan_row()
    price = price_row(plan.id, **{field: value})

    with pytest.raises(ValueError, match=message):
        loader_for(FakeSession([plan], [price])).load()


def test_inactive_plan_and_price_remain_in_catalogue_as_inactive():
    plan = plan_row(active=False)
    price = price_row(plan.id, active=False)

    catalogue = loader_for(FakeSession([plan], [price])).load()

    assert catalogue.get_plan("PREMIUM").active is False
    with pytest.raises(ValueError, match="Billing plan is inactive"):
        catalogue.get_price(plan_code="PREMIUM", billing_interval="month")
