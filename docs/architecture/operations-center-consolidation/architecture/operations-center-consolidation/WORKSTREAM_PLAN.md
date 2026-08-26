# OC-CONSOLIDATION Workstream Plan

## Objective

Consolidate the existing EasyChatBot Operations Center implementations into one maintainable operational surface.

## Phase 1 — Inventory

Identify every:

- frontend Operations Center route
- backend Operations Center router
- dashboard service
- dashboard model/contract
- health service
- incident service
- operational event service
- provider dashboard implementation
- navigation entry
- API client
- legacy dashboard
- static dashboard
- hackathon dashboard

Record the owning component and current usage.

## Phase 2 — Canonical Architecture

Confirm:

- Next.js frontend = canonical product UI
- `/operations-center` = canonical UI route
- FastAPI = canonical backend
- `/api/operations-center/*` = canonical API namespace
- WS-21.8 health snapshot = health source
- WS-21.9 events/incidents = operational event source
- WS-21.10 dashboard contract = dashboard aggregation contract

## Phase 3 — Capability Mapping

For every duplicate implementation:

```text
Capability
    |
    +-- Exists in canonical implementation?
    +-- Exists only in legacy implementation?
    +-- Better implementation elsewhere?
    +-- Tests available?
    +-- Production dependency?
    +-- Migration required?
```

No functionality is removed solely because it is duplicated.

## Phase 4 — Migration

Move useful capabilities into the canonical Operations Center.

Migration must follow:

```text
Existing capability
        |
        v
Adapter / migration
        |
        v
Canonical service/component
        |
        v
Regression tests
        |
        v
Integration verification
```

## Phase 5 — Verification

Run:

1. unit tests
2. integration tests
3. Operations Center tests
4. health tests
5. incident tests
6. frontend build
7. frontend smoke test
8. API smoke test
9. security checks
10. regression suite

## Phase 6 — Retirement

Only after successful verification:

- remove obsolete routes
- remove obsolete dashboard components
- remove obsolete API aliases
- remove obsolete frontend implementations
- remove stale documentation
- remove unused dependencies

Retirement must be incremental and reversible.

## Definition of Done

The workstream is complete only when:

- one canonical Operations Center exists
- no competing production dashboard exists
- all retained capabilities are reachable from `/operations-center`
- `/api/operations-center/*` is the canonical operational API
- duplicate implementations are retired or explicitly documented as temporary
- desktop, tablet and mobile layouts are verified
- existing WS-21.5+ health/operations tests remain green
- frontend and backend builds pass
- security review passes
- operational user-reference controls remain intact
- private classroom and announcement-group monitoring remain separated
