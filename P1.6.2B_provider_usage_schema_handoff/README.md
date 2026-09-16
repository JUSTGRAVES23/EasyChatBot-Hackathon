# P1.6.2B Provider Usage Ledger Schema Handoff

## Ownership

Database schema/migration:
- Academy-owned migration process

Application:
- EasyChatBot provider usage domain
- ProviderUsageEvent
- ProviderUsageRecord
- PostgreSQLProviderUsageRepository
- usage capture
- tests

## Current database state

The inspected PostgreSQL database currently reports:

provider_usage_events = NOT FOUND

Therefore this handoff provisions the initial table.

## Required semantics

Provider telemetry is nullable where the provider cannot supply it.

Important distinction:

- NULL = usage/telemetry unknown or unavailable
- 0 = provider explicitly reported zero
- total_tokens = provider-reported total when available
- provider_request_id = provider request identifier when available

## Execution boundary

Do NOT execute this SQL from EasyChatBot.

Do NOT run:

    alembic upgrade head
    alembic upgrade heads
    alembic merge

from the EasyChatBot repository for this migration.

The migration must be applied by the Academy-owned database migration process.

## Post-migration acceptance

After the migration owner confirms deployment:

1. Verify provider_usage_events exists.
2. Verify nullable telemetry columns.
3. Verify total_tokens exists.
4. Verify provider_request_id exists.
5. Run the P1.6.2B PostgreSQL round-trip test.
6. Verify no unrelated Academy migrations were changed.
