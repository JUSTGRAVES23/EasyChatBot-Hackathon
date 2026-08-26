# Decision Log

## Decision 001 — Single Operations Center

**Status:** Approved

EasyChatBot will maintain one canonical operational interface.

**Canonical UI:**

`/operations-center`

**Canonical product frontend:**

Existing Next.js application.

**Canonical backend:**

Existing FastAPI application.

**Canonical API namespace:**

`/api/operations-center/*`

## Decision 002 — No immediate deletion

Existing Vite/hackathon and legacy implementations will not be deleted immediately.

Reason:

- functionality may exist only there
- tests may depend on them
- migration risk must be understood
- working software must not be broken

## Decision 003 — WS-21.11 is integrated, not deployed separately

The WS-21.11 visual dashboard is a design/prototype source.

Its final destination is the existing `/operations-center` application.

It must not create a second production dashboard.

## Decision 004 — Centralization is a long-term architectural constraint

Future operational capabilities must be added as modules inside the canonical Operations Center unless a documented architectural exception is approved.
