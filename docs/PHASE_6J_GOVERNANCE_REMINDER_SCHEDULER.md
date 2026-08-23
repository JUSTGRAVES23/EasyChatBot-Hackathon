# Phase 6J — Governance Reminder & Escalation Scheduler

## Objective

Add controlled follow-up for privacy governance cases that remain pending.
The scheduler is a reminder/escalation mechanism only.

## Human governance boundary

The scheduler MUST NOT:
- approve a case;
- reject a case;
- request changes;
- modify the Privacy Change Registry;
- modify the Governance Case Registry.

The DPO/GRC reviewer remains the decision authority.

## Flow

Privacy Governance Case
→ scheduler evaluates policy
→ reminder due?
→ controlled email
→ human reviews case/change evidence
→ human explicitly records decision
→ existing decision service
→ existing Excel/API synchronization

## Decision Proposal Summary

Every reminder provides a concise summary containing:
- Case ID
- Change ID
- title
- risk
- automated validation status
- current governance status
- required DPO/GRC roles
- explicit decision options

It must clearly state that the message is not an approval.

## Initial Beta policy

Default:
- first reminder after 24 hours pending;
- repeat reminder after another 24 hours;
- no reminder for APPROVED or BLOCKED cases.

These are configuration values, not hard-coded governance decisions.

## Production note

The included reminder state is in-memory for Beta testing. Before production/multi-process deployment, replace it with a persistent repository with a uniqueness/idempotency constraint such as:

(case_id, reminder_type, reminder_period)

This prevents duplicate emails after process restart or multiple scheduler workers.

## Integration

Do not create a second scheduler framework if the repository already provides shared scheduling infrastructure.

Register `PrivacyGovernanceReminderScheduler.run_once()` as a job in the existing scheduler runtime through an adapter appropriate to that runtime.

The scheduler should run at a controlled cadence (for example hourly) while the policy decides whether an individual case is due.

## Verification

Run:

pytest tests/application/test_privacy_governance_reminder_scheduler.py -q

Then perform an integration test with:
1. one pending case older than the reminder threshold;
2. one non-overdue pending case;
3. one APPROVED case;
4. one BLOCKED case;
5. a second scheduler pass to verify duplicate suppression.

## DPO review workflow

When the reminder arrives, the DPO should:
1. Open the governance case.
2. Confirm the Change ID links to the authoritative Privacy Change.
3. Review automated validation evidence.
4. Review risk and applicable privacy evidence.
5. Select APPROVE, REJECT, or REQUEST_CHANGES.
6. Record reviewer identity and rationale in the governance system.

The scheduler itself must not recommend one of those outcomes.
