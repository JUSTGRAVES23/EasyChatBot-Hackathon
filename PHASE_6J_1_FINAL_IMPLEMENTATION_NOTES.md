# Phase 6J.1 — Final Governance Reminder

## Decision

The existing "Approval Required" email remains the initial governance
escalation message.

This new email is specifically a **reminder** and is deliberately shorter.

### Reminder flow

Pending DPO/GRC case
    ↓
Reminder interval reached
    ↓
Cooldown check
    ↓
Concise reminder email
    ↓
REVIEW THIS CASE →
    ↓
Privacy Governance Center
    ↓
Human decision
    ↓
Governance registry
    ↓
Excel evidence

## CTA

The reminder has exactly one primary CTA:

REVIEW THIS CASE →

It does not provide Approve / Reject / Request Changes buttons in email.

That keeps the authoritative governance action inside the controlled
application.

## URL

The URL is configuration-driven:

APP_BASE_URL=http://127.0.0.1:5173

Result:

http://127.0.0.1:5173/privacy-governance/{case_id}

For production, replace APP_BASE_URL with the approved production application
origin.

## Logo

The supplied EasyChatBot logo is included as:

backend/app/application/privacy/email/assets/easychatbot_logo.png

The email references it through CID:

easychatbot-governance-logo

The local Windows source path is deliberately NOT embedded in application
configuration.

## Scheduler

Do not create another AsyncIOScheduler.

The PrivacyGovernanceReminderScheduler is a workflow intended to be invoked by
the existing CybersecuritySchedulerFactory / CybersecurityAPSchedulerAdapter.

Before applying factory changes to the repository, run the existing scheduler
regression suite and inspect the current email adapter signature. The adapter
must support the HTML body and inline asset, or the governance email adapter
must translate the generic message into the provider's native format.

## Important

This package does not change the existing initial approval-required email.
That will be a separate later UX/template refinement.
