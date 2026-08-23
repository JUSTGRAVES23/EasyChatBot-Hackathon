# Phase 6C — Real Privacy Governance Case Flow

## Beta objective

Connect the existing privacy governance processing to one shared composition root:

```text
Privacy Change
    ↓
Privacy Governance Gate
    ↓
Privacy Governance Case Service
    ↓
Shared Case Registry
    ↓
Dashboard Service
    ↓
FastAPI Governance API
    ↓
Operations Center UI
```

Validation remains deterministic and external to the orchestration service. The
Beta flow accepts the existing validation result as `automated_validation_passed`.

## Human approval

No approval HTTP endpoint is introduced in Phase 6C.

Human decisions remain application-level operations through
`PrivacyGovernanceCaseService`, preserving the existing governance boundary.

## Beta persistence

Registries remain in-memory:

- PrivacyChangeRegistry
- PrivacyGovernanceCaseRegistry
- PrivacyApprovalRegistry

This is intentional for the Beta demonstration.

## Full-platform migration

The registry contracts should later be backed by repositories (for example,
PostgreSQL) without changing:

- the frontend API paths;
- the dashboard service contract;
- the case service public methods;
- the governance flow boundary.

## Running the tests

```powershell
pytest tests\application\test_privacy_governance_flow_service.py -q
pytest tests\application\test_privacy_governance_composition_shared_state.py -q
```

Then run the existing privacy/API suite.
