# WS-17 Validation Record

## Workstream

WS-17 — Beta Telegram Persistence & Session Integrity

## Validation Status

Status: NOT STARTED

## Environment

Project:
EasyChatBot-Hackathon

Runtime:
Python 3.13

Primary interface:
Telegram Beta private classroom

Persistence:
PostgreSQL

AI Runtime:
ConversationRuntime

## Baseline

Existing Beta Telegram test suite:

Command:

python -m pytest `
  ".\backend\tests\beta_access\" `
  ".\tests\beta_access\" `
  ".\tests\interfaces\telegram\" `
  ".\tests\infrastructure\telegram\" `
  -q

Expected:

All existing tests pass.

## Validation Matrix

### WS17-01 — Conversation Persistence

Objective:

Verify learner and assistant events are persisted.

Status:

NOT STARTED

Evidence:

TBD

---

### WS17-02 — Conversation ID Integrity

Objective:

Verify learner and assistant events belonging to the same interaction
share the correct conversation_id.

Status:

NOT STARTED

Evidence:

TBD

---

### WS17-03 — World Isolation

Objective:

Verify events remain associated with the correct learning World.

Status:

NOT STARTED

Evidence:

TBD

---

### WS17-04 — Telegram Identity Isolation

Objective:

Verify conversation persistence uses the pseudonymised Telegram identity
and does not store the raw Telegram user ID.

Status:

NOT STARTED

Evidence:

TBD

---

### WS17-05 — Privacy Governance

Objective:

Verify every persisted conversation event contains:

privacy_hash_version

and:

retention_policy_id

Status:

NOT STARTED

Evidence:

TBD

---

### WS17-06 — Conversation History

Objective:

Verify recent conversation history can be retrieved correctly and in
chronological order.

Status:

NOT STARTED

Evidence:

TBD

---

### WS17-07 — Duplicate Binding Protection

Objective:

Verify an already-connected Telegram identity cannot be incorrectly
reassigned to another Beta user.

Status:

NOT STARTED

Evidence:

TBD

---

### WS17-08 — Runtime Restart

Objective:

Stop and restart the Telegram runtime and verify that existing Beta
access and Telegram identity binding remain valid.

Status:

NOT STARTED

Evidence:

TBD

---

### WS17-09 — Real Telegram Smoke Test

Objective:

Send a real learner message through the Telegram private classroom after
runtime restart.

Test message:

Bonjour

Expected:

A valid French response is returned by the assigned character/runtime.

Status:

NOT STARTED

Evidence:

TBD

---

## Security Review

### Raw Telegram Identity

Expected:

NOT persisted in conversation_events.

Status:

NOT STARTED

---

### Pseudonymisation

Expected:

telegram_user_hash is persisted instead of raw Telegram user ID.

Status:

NOT STARTED

---

### Governance Metadata

Expected:

privacy_hash_version is mandatory.

Status:

NOT STARTED

---

### Retention Policy

Expected:

retention_policy_id is mandatory.

Status:

NOT STARTED

---

## Architecture Review

Expected flow:

Telegram
    ->
Interface
    ->
Beta Access
    ->
Application
    ->
Conversation Runtime
    ->
Provider
    ->
Persistence
    ->
Telegram

Status:

NOT STARTED

## Test Results

Baseline:

TBD

WS-17:

TBD

## Production Smoke Result

TBD

## Reviewer Sign-Off

Architecture:

PENDING

Security:

PENDING

Persistence:

PENDING

Testing:

PENDING

Production Readiness:

PENDING

Final Status:

NOT COMPLETE
