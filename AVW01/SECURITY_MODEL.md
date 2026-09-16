# AVW-01 Security Model

## Required controls
- No raw verification token in HTTP responses.
- No raw verification token in ordinary logs.
- Verification tokens remain hashed in persistence.
- Tokens expire and are single-use.
- Resend must not disclose whether an account exists.
- Resend must be rate-limited.
- Provider failure never authenticates the account.
- Provider credentials remain configuration-only.
- Existing session authentication remains unchanged.
- Existing Project Control authorization remains unchanged.

## Generic resend response
`If an account requires email verification, a verification email has been requested.`

## Safe operational events
Suggested events: `auth.verification.issue`, `auth.verification.delivery`, `auth.verification.resend`, `auth.verification.completed`, `auth.verification.rate_limited`.

Never record passwords, password hashes, raw tokens, API keys or session IDs.
