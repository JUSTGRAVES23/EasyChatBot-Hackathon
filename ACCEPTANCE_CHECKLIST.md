# Acceptance Checklist

- [x] Beta user model contract unified
- [x] Token model contract unified
- [x] Telegram binding model contract unified
- [x] Token hashing at application boundary
- [x] Token expiry
- [x] Single-use token
- [x] Beta approval guard
- [x] Email verification guard
- [x] World assignment guard
- [x] Telegram identity uniqueness guard
- [x] Private-chat-only binding
- [x] Active classroom gate
- [x] Email/deep-link workflow
- [x] PostgreSQL persistence adapter
- [x] Alembic migration
- [x] End-to-end in-memory regression tests

## Integration verification required in target repository

1. Confirm the existing Alembic head and set `down_revision`.
2. Wire the PostgreSQL repositories into the existing application composition.
3. Wire `BetaTelegramStartHandler` into the existing Telegram application.
4. Replace the in-memory email sender with the existing production email sender.
5. Run the existing full test suite.
6. Run the migration against the intended PostgreSQL database.
