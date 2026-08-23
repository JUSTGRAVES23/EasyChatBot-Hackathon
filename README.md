# EasyChatBot Phase 6H.1 — Case ↔ Change Relationship

Focused implementation package for preserving traceability between a privacy
governance case and its authoritative privacy change.

## Files

- `backend/app/application/privacy/privacy_governance_case.py`
- `backend/app/application/privacy/privacy_governance_case_change_link.py`
- `backend/app/application/privacy/privacy_governance_case_service.py` — focused
  patch instruction showing the required `change_id=change_id` constructor line
- `tests/application/test_privacy_governance_case_change_link.py`
- `docs/PHASE_6H1_CASE_CHANGE_RELATIONSHIP.md`

## Integration

Do not replace the live 6G composition or decision service. Add the
`change_id=change_id` line to the existing `PrivacyGovernanceCaseService`
`create_case()` constructor call, then run the focused and existing regression
suites.
