# Phase 6J — Governance Operational Follow-up

## Purpose

This slice turns the already-tested governance reminder scheduler into a
clean application job that can be invoked by the **existing platform scheduler
runtime**.

It does **not** create a second scheduler framework.

## Architecture

```text
Existing Platform Scheduler
          |
          v
PrivacyGovernanceOperationalFollowUp.run_once()
          |
          v
PrivacyGovernanceReminderScheduler
          |
          +--> GovernanceReminderPolicy
          |
          +--> Governance Case Registry (read-only)
          |
          +--> Controlled Governance Email
          |
          +--> Reminder State / Idempotency
```

The existing governance decision path remains separate:

```text
DPO/GRC UI
    |
    v
POST decision
    |
    v
Decision Service
    |
    +--> Governance Registry
    |
    +--> Approval Evidence
    |
    +--> Excel Sync
```

The scheduler never calls the decision service.

## Operational behavior

Default policy:

- first reminder after 24 hours pending;
- repeat reminder after another 24 hours;
- no reminder for APPROVED;
- no reminder for BLOCKED.

The scheduler cadence and the reminder policy are intentionally separate.
For example, the existing scheduler may invoke this job hourly while the
policy decides whether a particular case is due.

## DPO operating model

A reminder contains a decision proposal summary:

- Case ID
- Change ID
- title
- risk
- automated validation result
- current governance status
- required reviewer roles
- available decision options

The message explicitly states that it is not an approval.

The DPO/GRC reviewer must open the case, review the authoritative evidence,
and explicitly record the decision in the governance system.

## Security / governance boundary

This job MUST NOT:

- approve;
- reject;
- request changes;
- alter the Privacy Change Registry;
- alter the Governance Case Registry;
- treat email receipt/reply as approval;
- bypass authenticated human decision controls.

## Integration rule

Register `PrivacyGovernanceOperationalFollowUp.run_once` with the repository's
existing scheduler runtime.

Do not add another scheduler loop, background scheduler, or competing
scheduler factory.

The exact registration point should be the existing scheduler factory/runtime
used by the project. This package intentionally provides the application job
and contract without modifying cybersecurity scheduling code.

## Production readiness

The current reminder state may be in-memory for Beta.

Before multi-process or restart-sensitive production deployment, replace it
with a persistent store enforcing idempotency, for example:

```text
(case_id, reminder_type, reminder_period)
```

The persistent implementation should record:

- case_id
- reminder type
- scheduled/effective period
- sent_at
- recipient
- message/evidence identifier
- delivery status
- failure information

## Verification

Run:

```powershell
pytest tests\application\test_privacy_governance_operational_followup.py -q
```

Then run the existing Phase 6J scheduler tests and the full governance suite.

A production integration test should demonstrate:

1. pending case becomes due;
2. existing scheduler invokes the job;
3. one controlled reminder is sent;
4. a second invocation does not duplicate it;
5. DPO/GRC decision remains untouched;
6. explicit human decision still flows through the existing API;
7. decision updates registry and Excel evidence.
