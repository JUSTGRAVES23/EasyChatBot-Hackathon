# AVW-01 API Contract

## POST /auth/register
Unauthenticated. Creates an unverified account and attempts verification-email delivery. Never returns a verification token or URL.

## POST /auth/resend-verification
Request:
```json
{"email":"user@example.com"}
```

Use a generic outward response so account existence is not disclosed. Provider errors remain internal operational information.

## POST /auth/verify-email
Existing endpoint remains authoritative for token consumption and verification.

## POST /auth/login
Existing behavior remains: active account, verified email and valid password are required.
