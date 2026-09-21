# W19.2 Verification Pack

This package is the next controlled step after the W19.2 implementation.

## Purpose

Verify the **deployed PostgreSQL schema** and run the existing W19.2/W19.1
targeted regression suite before W19.2 acceptance.

The package is intentionally **verification-only**. It does not:
- change `WorldAccessService`;
- change `LearningWorldModel`;
- change Beta Telegram/private-chat behaviour;
- call the Telegram API;
- grant World access from Telegram membership;
- rewrite an already-applied Alembic migration;
- introduce a second Telegram client or publication boundary.

## Schema contract checked

```text
users.id (UUID)
    |
    +--> world_telegram_memberships.user_id
          FK -> users.id
          ON DELETE CASCADE

world_telegram_destinations.id (UUID)
    |
    +--> world_telegram_memberships.destination_id
          FK -> world_telegram_destinations.id
          ON DELETE RESTRICT
```

The verifier checks:
- table existence;
- UUID type for `id`, `destination_id`, and `user_id`;
- expected nullability;
- primary key;
- UNIQUE(destination_id, user_id);
- status CHECK constraint;
- destination foreign key and `RESTRICT`;
- user foreign key and `CASCADE`;
- expected destination/user indexes.

## Run

Extract this package into the project, then from:

```text
C:\AI Folder\EasyChatBot-Hackathon\backend
```

run:

```powershell
python ".\scripts\verify_w19_2_schema.py"
```

Then run the complete targeted sequence:

```powershell
& "C:\Users\barbe\Downloads\W19_2_Verification_Pack\RUN_W19_2_VERIFICATION.ps1"
```

The PowerShell path above assumes the ZIP is extracted there. Alternatively run
the commands inside the script manually.

## Acceptance boundary

A schema PASS plus the targeted tests passing establishes the next verification
gate. A real PostgreSQL repository round-trip test should be added only after
the project's existing integration-test database fixture/factory is inspected;
this pack deliberately does not invent a new fixture or guess required fields
on the authoritative `users`/`learning_worlds` models.

W19.3 should remain blocked until W19.2 is accepted and reviewed.
