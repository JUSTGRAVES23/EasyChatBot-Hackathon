# Announcement Execution Persistence — Data Protection Inventory

## Ownership

This persistence object belongs to WS-22 Announcement Operations execution.
It is not the WS-21 Chat Operations event store and must not be used to store
learner conversation data.

## Technology distinction

- SQLAlchemy: ORM/database-access layer used by the application.
- PostgreSQL: persistent database server.
- Alembic: schema migration/versioning mechanism.

## Persisted fields

| Field | Purpose | Sensitive content |
|---|---|---|
| publication_id | Links execution to WS-22 publication | Identifier only |
| idempotency_key | Prevents duplicate execution | Operational identifier |
| correlation_id | Traceability across an operation | Operational identifier |
| attempt | Retry/execution tracking | Operational |
| status | Execution state | Operational |
| provider_message_id | Reconciliation with publication provider | Provider identifier |
| error_code | Stable operational failure classification | Controlled code only |
| created_at | Auditability | Timestamp |
| updated_at | Auditability | Timestamp |

## Explicit exclusions

The execution table must not contain:
- learner messages or conversation content
- prompts
- model responses
- API keys or provider credentials
- Telegram bot tokens
- raw provider payloads
- raw exception text
- unnecessary personal data

## Workstream boundary

WS-21 operational event data remains owned by WS-21.
WS-22 publication content remains owned by the publication/template domain.
This table records execution state only.

## Retention

Retention is intentionally not hard-coded in this implementation. The final
retention period should be established in the platform data-retention policy
and applied consistently with legal, audit, and operational requirements.
