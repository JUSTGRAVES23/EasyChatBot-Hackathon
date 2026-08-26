# Operations Center Consolidation Workstream

**Workstream ID:** OC-CONSOLIDATION  
**Purpose:** Establish one canonical EasyChatBot Operations Center without disrupting currently working functionality.

## Decision

The long-term canonical operational UI is:

`/operations-center`

The canonical product frontend is the existing Next.js application on port `3000`.

The canonical backend is the existing FastAPI application on port `8000`.

The canonical Operations Center API namespace is:

`/api/operations-center/*`

This workstream does not immediately delete or rewrite existing implementations. It inventories, compares, migrates, verifies, and only then retires duplicates.

## Current target

```text
EasyChatBot
    |
    +-- Next.js product frontend :3000
    |       |
    |       +-- /operations-center
    |
    +-- FastAPI backend :8000
            |
            +-- /api/operations-center/*
```

The existing Vite/hackathon frontend and legacy routes remain temporarily supported until their useful functionality has been assessed and migrated.

## Engineering rule

Do not create another Operations Center route, dashboard application, or competing API namespace while this workstream is open.

## Safety

Consolidation must preserve:

- existing working features
- existing API contracts unless an explicit migration is approved
- authorization boundaries
- operational auditability
- private-classroom / announcement-group separation
- controlled user identification
- secret and learner-content protection
