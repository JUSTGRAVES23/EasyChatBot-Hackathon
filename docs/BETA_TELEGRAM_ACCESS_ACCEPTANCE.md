# Acceptance criteria

- Registration precedes Beta access.
- Email verification is mandatory.
- Beta approval is explicit.
- Classroom email is sent only after approval.
- Token is cryptographically random.
- Token expires after 15 minutes by default.
- Token is single-use.
- Telegram identity cannot belong to two Academy users.
- Private Telegram chat is used; no per-user Telegram group/channel is created.
- Selected Learning World is required for ACTIVE.
- Unauthorized Telegram users are blocked before lesson/AI processing.
- Existing TELEGRAM_CONNECTED event remains the event boundary.
- Token persistence is durable.
- Unit and end-to-end tests cover the access workflow.
