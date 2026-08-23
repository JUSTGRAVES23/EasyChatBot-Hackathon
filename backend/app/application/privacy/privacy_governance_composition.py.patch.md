# Phase 6H.2 integration patch

The runtime composition remains the single source of truth.

Add the existing Excel synchronizer to the process-wide composition and expose
a runtime sync service:

```python
from .privacy_governance_excel_sync import PrivacyGovernanceExcelSync
from .privacy_governance_runtime_sync import PrivacyGovernanceRuntimeSync
```

After creating `case_service` and `dashboard_service`, construct the existing
Excel adapter and runtime bridge using the SAME registries/services:

```python
excel_sync = PrivacyGovernanceExcelSync(
    case_registry=case_registry,
    approval_registry=approval_registry,
)

runtime_sync = PrivacyGovernanceRuntimeSync(
    case_service=case_service,
    excel_sync=excel_sync,
)
```

Add to `PrivacyGovernanceComposition`:

```python
excel_sync: PrivacyGovernanceExcelSync
runtime_sync: PrivacyGovernanceRuntimeSync
```

Do not create another composition or another registry.

The runtime topology must remain:

Privacy Change
→ Validation
→ Governance Gate
→ Case Service
→ Shared Registries
→ Runtime Sync
→ Existing Excel Tracker
