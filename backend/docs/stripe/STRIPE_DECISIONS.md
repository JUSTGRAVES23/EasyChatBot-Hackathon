# Architecture decisions

## ADR-001 — Stripe as initial payment provider

Decision: Stripe.

Reasoning:
- strong Checkout/Billing/Customer Portal primitives;
- mature webhook model;
- good fit for SaaS subscriptions and one-time purchases;
- allows EASYWORLD to avoid handling raw card data;
- clean provider-adapter architecture.

## ADR-002 — TEST mode before LIVE

Decision: implement and validate in Stripe TEST mode while EASYWORLD remains free.

## ADR-003 — Stripe is not the entitlement system

Decision: Stripe owns payment/subscription transaction state; EASYWORLD owns product access and entitlements.

## ADR-004 — Webhooks, not redirects, confirm payment state

A successful browser redirect is not sufficient to grant paid access. Verified webhook events drive state synchronization.

## ADR-005 — Customer Portal over custom billing management

Use Stripe Customer Portal for payment method, invoice and subscription management where the product requirements allow it.
