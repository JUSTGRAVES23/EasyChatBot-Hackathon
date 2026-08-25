# WS-02 Security Review

## Controls

### Authentication and authorisation

Only the designated administrator may publish.

The channel is not a user command surface.

### Secrets

The Telegram bot token must come from the deployment secret store or
environment configuration. Never commit it.

### Least privilege

The classroom bot should not be granted channel administration rights.

The eventual publishing identity should have only the Telegram permissions
required to publish announcements.

### Injection

Announcement content must be treated as untrusted input. Beta 1 uses
controlled Markdown formatting. Future rich formatting must introduce
explicit escaping tests.

### Accidental publication

Publishing defaults to disabled.

`TELEGRAM_ANNOUNCEMENT_PUBLISHING_ENABLED=false`

Publication requires explicit enablement.

### Auditability

Each successful publication produces a PublicationRecord containing:
- channel
- Telegram message identifier
- UTC publication timestamp
- announcement type

A production persistence implementation can later store these records.

### AI governance

No AI agent is permitted to autonomously publish to the Beta channel in
Beta 1.

AI may assist an administrator in drafting content in a future capability,
but publication remains an explicit controlled action.
