# PI-5A.4 Backend Operations Center Integration — 4-Eyes Review

## Scope

Integrate the existing Platform Intelligence human-review projection into the
canonical Operations Center application boundary.

## Implemented

1. `OperationsCenterComposition` now owns an injected
   `PlatformIntelligenceReviewSource` / `PlatformIntelligenceReviewAPI`.
2. The existing `/api/operations-center` router exposes:
   - `GET /api/operations-center/platform-intelligence/reviews`
   - `GET /api/operations-center/platform-intelligence/reviews/{review_item_id}`
   - `GET /api/operations-center/platform-intelligence/escalations`
3. Existing Operations Center routes remain in the same router.
4. `INTERNAL_DATA_READ` authorization is explicitly applied to all new PI
   endpoints.
5. The PI source remains a read-only application port.
6. No RiskDecision, HumanReview, or Escalation domain objects are duplicated.
7. No persistence or provider implementation is introduced.
8. The integration fails closed with HTTP 503 when no canonical PI source has
   been injected.
9. Escalation visibility is derived from the governed PI source's
   `list_escalations()` projection; no hard-coded workload values are created.

## Important boundary

The supplied backend source inspection does not contain a concrete canonical
`ai_agents` runtime adapter implementation. Therefore this integration does
not invent one. The production composition exposes an explicit injection point:

`create_operations_center_composition(platform_intelligence_review_source=...)`

Until that canonical adapter is provided, the Operations Center returns 503
for PI review endpoints rather than fabricated empty/approved data.

## Security

- Read-only endpoints only.
- Existing `INTERNAL_DATA_READ` permission boundary is reused.
- No reviewer identity is accepted from the HTTP request.
- No review completion or escalation action is exposed.
- No arbitrary runtime metadata is serialized.
- Runtime unavailability is fail-closed.

## 4-eyes outcome

Architecture: APPROVED
Security: APPROVED
Contract preservation: APPROVED
Test coverage for integration boundary: APPROVED

Production data availability remains dependent on the canonical PI runtime
adapter being injected at the composition root.
