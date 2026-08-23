# Beta Telegram Access Architecture

Reuse the existing `users` identity and World assignment. Add only `beta_connection_tokens`.

Lifecycle:
Registration -> email verification -> Beta approval/invitation -> World assignment -> token -> invitation email -> Telegram deep link -> `/start <token>` -> validation -> Telegram binding -> private-chat gate -> active classroom.

Security invariants:
- raw tokens are never persisted
- SHA-256 hashes are persisted
- tokens expire and are one-time use
- existing unique `users.telegram_id` protects identity uniqueness
- `active_world_id` is mandatory
- classroom access is private-chat only

Announcement channel is separate and administrator-controlled. Beta users must not receive posting permission.
