# Phase 6H.2 decision integration

The decision service remains authoritative for DPO/GRC decisions.

After `record_decision()` updates the shared change and case registries,
the runtime integration should project the resulting case to Excel.

Preferred production boundary:

```python
decision_service
    ↓
shared registries
    ↓
runtime_sync.sync_decision(case_id)
```

Do not make Excel responsible for approving, rejecting, or requesting changes.

If the existing application wiring supports dependency injection, inject the
runtime sync port into the decision orchestration layer. Otherwise, perform
the projection from the process-wide governance orchestration boundary after
`record_decision()` returns.

The important invariant is:

1. Decision is recorded first.
2. Shared registries are updated.
3. Excel is updated from authoritative state.
4. Excel failure must never turn an already-recorded governance decision into
a different governance decision.

A production implementation should log/surface synchronization failure and
provide retry/reconciliation rather than rollback the governance decision.
