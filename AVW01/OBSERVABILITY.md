# AVW-01 Observability

Suggested structured events:
- `auth.verification.issue`
- `auth.verification.delivery`
- `auth.verification.resend`
- `auth.verification.completed`
- `auth.verification.rate_limited`

Safe fields include status/outcome, provider identifier, correlation ID and coarse reason code.

Never log raw verification tokens, passwords, password hashes, session IDs or provider credentials.
