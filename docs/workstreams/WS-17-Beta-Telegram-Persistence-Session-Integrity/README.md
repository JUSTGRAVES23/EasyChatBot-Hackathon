# WS-17 — Beta Telegram Persistence & Session Integrity

## Objective

Verify that the real Beta Telegram classroom maintains correct persistence,
identity isolation, World isolation, governance metadata, and continuity
across runtime restarts.

## Scope

### 1. Conversation history
Verify that learner and assistant events are persisted correctly and can
be retrieved in chronological order.

### 2. User isolation
Verify that one Beta learner cannot access another learner's conversation
history.

### 3. Telegram identity isolation
Verify that Telegram identities remain bound to the correct Beta users.

### 4. World isolation
Verify that conversation context remains associated with the correct
learning World.

### 5. Restart resilience
Verify that stopping and restarting the Telegram runtime does not destroy
existing Beta access or Telegram bindings.

### 6. Governance persistence
Verify that every persisted conversation event contains:

- privacy_hash_version
- retention_policy_id

### 7. Duplicate binding protection
Verify that an already-connected Telegram identity cannot be incorrectly
reassigned to another Beta user.

## Architecture

Telegram
    |
    v
Private Chat Gate
    |
    v
Beta Access
    |
    v
Telegram Binding
    |
    v
Conversation Boundary
    |
    +-------------------+
    |                   |
    v                   v
Conversation Runtime   PostgreSQL
    |                   |
    v                   v
LLM Provider          Event Store
    |                   |
    +---------+---------+
              |
              v
       Telegram Response

## Acceptance Criteria

- [ ] Existing Beta Telegram test suite remains green.
- [ ] Learner conversation events persist successfully.
- [ ] Assistant conversation events persist successfully.
- [ ] Events retain the correct conversation_id.
- [ ] Events retain the correct world_id.
- [ ] Telegram identity is stored only in pseudonymised form.
- [ ] privacy_hash_version is persisted.
- [ ] retention_policy_id is persisted.
- [ ] Conversation history can be retrieved.
- [ ] User isolation is preserved.
- [ ] World isolation is preserved.
- [ ] Telegram binding survives runtime restart.
- [ ] Duplicate Telegram binding is rejected safely.
- [ ] Real Telegram smoke test succeeds after restart.
- [ ] No unrelated architecture changes are introduced.

## Engineering Rules

- Do not weaken PostgreSQL governance constraints.
- Do not bypass Beta Access controls.
- Do not allow Telegram handlers to access persistence directly.
- Do not store raw Telegram identity in conversation events.
- Do not create autonomous production side effects.
- Preserve provider independence.
- Keep infrastructure concerns inside the infrastructure layer.
- Keep orchestration inside the application/runtime layers.

## Definition of Done

WS-17 is complete only when:

1. Implementation is complete.
2. Existing tests pass.
3. Persistence/session behaviour is validated.
4. Security and privacy boundaries are verified.
5. Restart behaviour is demonstrated.
6. Real Telegram smoke test succeeds.
7. Git checkpoint is created.
8. Changes are reviewed for architecture and production readiness.
