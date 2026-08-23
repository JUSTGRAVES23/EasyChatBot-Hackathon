# Phase 6H.2 — Runtime-triggered Excel synchronization

## Objective

Project authoritative privacy governance state into the existing Excel tracker
using the process-wide governance composition.

## Architecture

```text
Privacy Change
    ↓
Validation
    ↓
Governance Gate
    ↓
Case Service
    ↓
Shared Registries
    ↓
Runtime Sync
    ↓
Existing Excel Tracker
```

For human decisions:

```text
DPO/GRC decision
    ↓
Decision Service
    ↓
Shared Registries
    ↓
Runtime Sync
    ↓
Approval Evidence
```

## Invariants

- The governance registries remain authoritative.
- Excel is an evidence/projection layer.
- No second governance registry is created.
- The API and processing flow use the same process-wide composition.
- A synchronization failure must not mutate the governance decision.
- Production should add retry/reconciliation for Excel failures.

## Next

After 6H.2 unit/integration validation, implement 6H.3 as the full lifecycle
Excel end-to-end test.
