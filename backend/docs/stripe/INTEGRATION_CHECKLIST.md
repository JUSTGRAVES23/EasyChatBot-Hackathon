# Integration checklist

Before merging into the canonical EASYWORLD codebase:

- [ ] Identify canonical backend application/router.
- [ ] Identify canonical user repository/model.
- [ ] Identify canonical authorization dependency.
- [ ] Identify canonical audit/event logging service.
- [ ] Identify canonical database migration system.
- [ ] Identify canonical configuration/secrets system.
- [ ] Add Stripe SDK using the project's existing dependency management.
- [ ] Register Stripe billing routes in the existing router.
- [ ] Implement a real database-backed payment event repository.
- [ ] Implement the real EASYWORLD entitlement service.
- [ ] Add authentication/authorization to checkout and portal endpoints.
- [ ] Validate requested price IDs against EASYWORLD's server-side catalogue.
- [ ] Never accept arbitrary Stripe price IDs from the browser without server-side validation.
- [ ] Add webhook signature verification.
- [ ] Add idempotency.
- [ ] Add tests for duplicate/replayed events.
- [ ] Configure Stripe TEST webhook endpoint.
- [ ] Run end-to-end TEST mode checkout.
- [ ] Confirm no paid entitlement is granted accidentally to the Free plan.
