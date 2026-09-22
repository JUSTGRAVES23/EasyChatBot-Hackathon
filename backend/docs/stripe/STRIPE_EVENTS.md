# Stripe event contract — initial set

Recommended initial events:

- checkout.session.completed
- payment_intent.succeeded
- payment_intent.payment_failed
- invoice.paid
- invoice.payment_failed
- customer.subscription.created
- customer.subscription.updated
- customer.subscription.deleted

## Event processing rules

1. Verify the Stripe signature before parsing business data.
2. Persist the provider event ID.
3. If the event ID was already processed, return success without repeating business effects.
4. Process business effects transactionally where possible.
5. Mark the event processed only after the business effect succeeds.
6. Keep failed events observable and retryable.
