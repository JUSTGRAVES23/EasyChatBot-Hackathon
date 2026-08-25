# Security Review — Initial Architecture

## Required controls

### Authentication / identity
- Bind Telegram identity to an approved application account.
- Make /start idempotent.
- Prevent account enumeration.
- Do not expose internal IDs unnecessarily.

### Authorization
- Check Beta approval before classroom access.
- Derive World visibility from application state.
- Never authorize World access from Telegram command parameters.

### Data protection
- Minimise personal information in Telegram messages.
- Do not expose another user's data.
- Do not place secrets or tokens in messages/logs.

### Abuse
- Rate-limit where required.
- Handle malformed updates.
- Protect deep links from being treated as proof of authorization.
- Validate issue-form inputs in the web application.

### Channel
- Bot must not have channel administrator privileges.
- Only administrator publishes official announcements.
- No user discussion/comments.

## Security gate
WS-02 implementation must not begin until the Head Engineer and Security/GRC reviewer confirm these controls are reflected in the actual repository architecture.
