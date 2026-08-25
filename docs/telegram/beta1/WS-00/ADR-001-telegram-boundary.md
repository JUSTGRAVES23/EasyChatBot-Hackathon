# ADR-001 — Telegram as a Thin Adapter

## Decision
Telegram integration is implemented as an infrastructure/interface adapter over application services.

## Rationale
This preserves:
- provider independence;
- testability;
- separation of concerns;
- reuse of application logic by web/API surfaces;
- easier replacement of Telegram later.

## Consequences
Telegram handlers remain small.
Business decisions belong to application/domain services.
Tests can exercise application services without Telegram.

## Rejected
Direct Telegram -> database/business logic.
