# WS-22.3.2.x.1 — PostgreSQL Restart & Idempotency Verification

Test-only integration slice.

Purpose:
- verify the already-applied `announcement_publication_executions` migration
  against real PostgreSQL;
- verify durable state survives a new SQLAlchemy repository/service instance;
- verify a successful idempotency key produces an IDEMPOTENT_REPLAY and does
  not call the publisher twice;
- verify provider message ID, correlation ID, attempt and status survive
  restart;
- verify failure state survives restart and a retry can be attempted.

No new domain/application/infrastructure abstraction is introduced.
No Telegram logic and no frontend changes.

The test requires `DATABASE_URL` and an async PostgreSQL SQLAlchemy driver
(`asyncpg`). It skips cleanly when DATABASE_URL is absent, because the test is
an integration test rather than a unit test.
