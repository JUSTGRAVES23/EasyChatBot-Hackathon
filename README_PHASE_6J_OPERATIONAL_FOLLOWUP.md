# EasyChatBot — Phase 6J Governance Operational Follow-up

This package is the operational integration slice for the already-tested
Phase 6J governance reminder scheduler.

It deliberately does not replace or modify the existing scheduler framework.

## Files

- `backend/app/application/privacy/privacy_governance_operational_followup.py`
  - application job / integration boundary
- `tests/application/test_privacy_governance_operational_followup.py`
  - five regression tests
- `docs/PHASE_6J_GOVERNANCE_OPERATIONAL_FOLLOWUP.md`
  - architecture, governance and production integration rules

## Install

From the EasyChatBot repository root:

```powershell
Copy-Item `
"C:\path\to\EasyChatBot_Phase_6J_Governance_Operational_Followup\*" `
"." `
-Recurse -Force
```

## Test

```powershell
pytest tests\application\test_privacy_governance_operational_followup.py -q
```

## Important

Do not create another scheduler service.

The existing scheduler runtime should invoke:

```python
job.run_once()
```

The job itself remains responsible only for governance operational
follow-up. Human governance decisions continue through the existing
decision API/service and Excel synchronization path.
