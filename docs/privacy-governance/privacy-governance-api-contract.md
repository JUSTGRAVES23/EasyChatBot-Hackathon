# Platform Privacy Governance API Contract

The API namespace is platform-wide:

```text
/api/privacy/governance
```

Do not create a Beta-specific API namespace.

## Read endpoints

### GET /api/privacy/governance/summary

Maps to:

```python
PrivacyGovernanceDashboardService.summary()
```

### GET /api/privacy/governance/status-chart

Maps to:

```python
PrivacyGovernanceDashboardService.status_chart()
```

### GET /api/privacy/governance/cases

Maps to:

```python
PrivacyGovernanceDashboardService.case_list()
```

### GET /api/privacy/governance/cases/{case_id}

Maps to:

```python
PrivacyGovernanceDashboardService.case_detail(case_id)
```

## Scope handling

The backend is authoritative for governance scope and enabled controls.

Beta 1 should be represented as a configuration/scope, not as a separate
API architecture.

Example conceptual configuration:

```python
PrivacyGovernanceConfiguration(
    scope="BETA_1",
    enabled_modules=[
        "PROCESSING_REGISTRY",
        "DATA_PROCESSING_MAP",
        "RETENTION",
        "PROCESSOR_REGISTRY",
        "DPIA_SCREENING",
        "PRIVACY_VALIDATION",
        "PRIVACY_CHANGE_CONTROL",
        "DPO_GRC_APPROVAL",
    ],
)
```

A future full-platform configuration can enable additional modules without
changing the UI API namespace.

## Security

All endpoints must use the existing Operations Center authentication and
authorisation controls.

The frontend must never receive:
- Resend API keys;
- SMTP credentials;
- provider secrets;
- unrelated learner personal data.

No write endpoint is defined by Phase 6.

Future decision endpoints must call application-level governance services and
must not permit direct registry/database mutation.
