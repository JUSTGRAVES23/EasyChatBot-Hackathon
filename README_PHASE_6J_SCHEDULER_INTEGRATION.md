# EasyChatBot Phase 6J — Governance Scheduler Integration

## Architecture

This phase does not create a second scheduler.

Existing infrastructure:

FastAPI lifespan
→ CybersecuritySchedulerRuntime
→ CybersecurityAPSchedulerAdapter
→ APScheduler

The adapter now optionally registers:

- `cybersecurity_daily_report`
- `cybersecurity_weekly_report`
- `privacy_governance_reminder`

The privacy reminder workflow remains in the privacy application layer.

## Governance flow

Pending case
→ reminder due
→ DPO/GRC notification
→ human opens case
→ human approves / rejects / requests changes

The reminder workflow never changes governance state.

## Reminder policy

Default reminder interval: 24 hours after `triggered_at`.

Eligible:
- `PENDING_DPO_GRC`

Not eligible:
- `APPROVED`
- `BLOCKED`
- any other governance status

## Controlled failures

Email failure returns `EMAIL_FAILED` and an error in the result. It does not change the case.

Missing email configuration returns `DUE` with `email_status=not_configured`.

## Integration note

The existing factory must inject a concrete implementation of
`PrivacyGovernanceReminderEmailPort` and pass the resulting
`PrivacyGovernanceReminderScheduler` to
`CybersecurityAPSchedulerAdapter(governance_reminder_workflow=...)`.

Do not create another APScheduler instance.
