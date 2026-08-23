# Phase 6H Integration

## Authority

The existing runtime remains authoritative:

- PrivacyGovernanceCaseRegistry
- PrivacyApprovalRegistry
- PrivacyGovernanceDecisionService

The Operations Center API continues to read the process-wide composition.

## Excel role

Excel is a downstream reporting/evidence projection. It must never be used
to decide whether a case is approved, blocked, or permitted to proceed.

## Sheets

### Privacy Governance Cases
One row per governance case.

### Approval Evidence
One row per explicit human decision.

### Governance Dashboard
Aggregate counts matching the Operations Center.

## Wiring

The recommended Beta wiring is:

    shared registries
          ↓
    PrivacyGovernanceTrackerProjection
          ↓
    PrivacyGovernanceExcelSync
          ↓
    workbook

Invoke the projection after case creation and after every DPO/GRC decision.

Do not put Excel I/O inside PrivacyGovernanceDecisionService itself.

## Production

Replace the Excel projection with a repository/event-backed reporting adapter
later without changing the FastAPI/UI contract.
