# Phase 6I — API → Governance → Excel Automatic Synchronization

## Objective

Close the application-level loop so human governance decisions made through
FastAPI automatically produce downstream Excel evidence.

## Authoritative flow

```text
Human
  ↓
FastAPI POST decision
  ↓
Privacy Governance Case Service
  ↓
Decision Service
  ↓
Shared Registries
  ↓
Runtime Excel Sync
  ↓
Privacy Governance Excel Sync
  ↓
Governance Tracker
```

Excel remains a downstream projection. It is not a source of truth.

## Files

- `privacy_governance_runtime_sync.py`
  - Existing runtime bridge.
- `privacy_governance_excel_runtime_config.py`
  - Controlled workbook path configuration.
- `privacy_governance_api_sync.py`
  - API-to-evidence synchronization coordinator.
- `privacy_governance.py`
  - Decision endpoints automatically invoke evidence synchronization.
- `test_privacy_governance_api_excel_sync.py`
  - API approval/rejection/request-changes integration coverage.
- `test_privacy_governance_api_excel_consistency.py`
  - Final workbook smoke/consistency check.

## Configuration

Optional environment variable:

```text
EASYCHATBOT_PRIVACY_GOVERNANCE_WORKBOOK
```

Default Beta path:

```text
backend/data/privacy_governance_tracker.xlsx
```

## Evidence failure policy

Governance state remains authoritative if Excel projection fails.

The API response explicitly reports:

```json
{
  "excel_sync": {
    "status": "FAILED",
    "workbook_path": "...",
    "error": "..."
  }
}
```

This avoids falsely claiming that evidence was synchronized.

For production, this should evolve into durable evidence-sync monitoring/outbox
processing rather than making the Excel file transactional with governance.

## Verification

Run:

```powershell
pytest tests\api\test_privacy_governance_api_excel_sync.py -q
pytest tests\application\test_privacy_governance_api_excel_consistency.py -q
```

Then run the complete existing Phase 6H suite.
