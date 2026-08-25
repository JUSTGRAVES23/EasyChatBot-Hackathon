# ADR-004 — Approved Beta Access and Telegram Identity Binding

## Decision
A user receives private classroom access only after application-level Beta approval.

Expected flow:

Registration
 -> Beta approval
 -> approval email
 -> Telegram bot link
 -> /start
 -> Telegram identity association
 -> approved classroom access

## Requirements
- /start must be idempotent.
- Existing approved users must not create duplicate application identities.
- Unapproved users must not gain classroom access.
- Telegram identity is an authentication/integration signal, not the source of World authority.

## Security
Never trust Telegram-supplied World identifiers as authorization.
