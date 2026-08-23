# Phase 6H.1 — Governance Case ↔ Privacy Change Relationship

## Purpose

Every runtime-created governance case must remain traceable to the privacy
change that caused it.

```text
Privacy Change Registry
        ↑
        │ change_id
        │
Governance Case Registry
        │
        ↓
Case ↔ Change Link Service
        ↓
Excel evidence projection
```

## Authority

- `PrivacyChangeRegistry` remains authoritative for the change.
- `PrivacyGovernanceCaseRegistry` remains authoritative for the case.
- `PrivacyGovernanceCaseChangeLinkService` only resolves the relationship.
- Excel remains a downstream reporting/evidence projection.

## Required runtime behavior

`PrivacyGovernanceCaseService.create_case()` should populate:

```python
change_id=change_id
```

when constructing `PrivacyGovernanceCase`.

This makes the relationship explicit without creating a second mapping store.

## Excel evidence

The existing `Privacy Governance Cases` sheet already reserves:

- Case ID
- Change ID
- Title
- Summary
- Risk
- Validation
- Governance Status

Phase 6H.1 therefore makes the existing `Change ID` column authoritative by
ensuring newly created cases populate it from the same `PrivacyChange` used by
the flow.

## Safety

This slice is read-only with respect to governance state. It does not approve,
reject, or execute privacy changes and it does not allow Excel to become a
source of truth.
