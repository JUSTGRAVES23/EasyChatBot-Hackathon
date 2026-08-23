# Phase 6G — Human Governance Decision Actions

## Scope

This slice adds explicit human governance decisions while preserving the
existing read-only dashboard and shared runtime composition.

### Flow

```text
Case Detail
   ↓
Human confirmation
   ↓
POST /api/privacy/governance/cases/{case_id}/{decision}
   ↓
PrivacyGovernanceCaseService
   ↓
PrivacyGovernanceDecisionService
   ↓
Shared approval/case/change registries
   ↓
Updated case + approval evidence
   ↓
Dashboard refresh
```

## Backend endpoints

- `POST /api/privacy/governance/cases/{case_id}/approve`
- `POST /api/privacy/governance/cases/{case_id}/reject`
- `POST /api/privacy/governance/cases/{case_id}/request-changes`

Request body:

```json
{
  "change_id": "PCR-E2E-001",
  "approval_id": "APR-DPO-E2E-001",
  "reviewer": "DPO Reviewer",
  "role": "DPO",
  "comment": "Privacy review completed."
}
```

Only `DPO` and `GRC` are accepted as roles.

## Frontend

`PrivacyGovernanceDecisionActions.tsx` provides:

- Approve as DPO
- Approve as GRC
- Reject
- Request changes
- confirmation before POST
- loading state
- API error state
- mobile-friendly action layout

The component is intentionally separate from the dashboard shell so the
existing Phase 6F visual design remains stable.

### Integration

Inside the existing case-detail drawer, render:

```tsx
<PrivacyGovernanceDecisionActions
  caseDetail={selectedCase}
  onDecisionCompleted={async (updatedCase) => {
    setSelectedCase(updatedCase);
    await refreshDashboard();
  }}
/>
```

The exact state setter/function names depend on the existing dashboard
implementation.

The case detail type must expose `change_id`. If the current detail API
does not expose `change_id`, add it to the backend dashboard-detail response;
do not derive it in the frontend.

## Security boundary

Beta currently accepts the reviewer identity in the request body because the
existing application has not yet established an authenticated identity
provider for this governance slice.

This is NOT production authorisation.

Before production:

```text
Authenticated user/session
        ↓
Server-side identity
        ↓
Role/permission check
        ↓
Decision service
```

The browser must not be trusted to assert that a person is a DPO/GRC.

## Important governance rules

- GET endpoints remain read-only.
- State changes use POST.
- Email delivery is never approval.
- AI output is never approval.
- Dashboard clicks are not approval until the explicit POST is confirmed
  and accepted by the backend.
- The backend remains authoritative for decision state.
- Rejection and request-changes transition the case to BLOCKED according to
  the existing application contract.
- DPO + GRC approval transitions a case to APPROVED according to the
  existing decision service.

## Validation

Backend:

```powershell
pytest `
  tests\api\test_privacy_governance_decisions_api.py `
  tests\application\test_privacy_governance_6g_lifecycle.py `
  -q
```

Frontend:

```powershell
npm test
npm run build
```

If the existing frontend package does not expose a test script, run the
configured Vitest command directly after confirming the package scripts.

## Production follow-up

The next security slice should integrate authenticated identity and
server-side authorisation. Do not expose the Beta demo endpoint in
production.
