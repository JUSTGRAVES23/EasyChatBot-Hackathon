# EasyChatBot — Authentication Verification Workflow (AVW-01)

This package defines the controlled completion of EasyChatBot's existing authentication verification lifecycle. It is an integration framework, not a parallel authentication system.

## Approved architecture
- Reuse PostgreSQL authentication persistence and existing verification-token lifecycle.
- Reuse `AuthenticationEmailService`.
- Reuse `EmailProviderManager` and `ResendEmailProvider`.
- Complete registration -> verification-email delivery.
- Add resend verification on the same workflow.
- Keep accounts unverified when delivery fails.
- Add enumeration resistance, rate limiting and safe diagnostics.
- Add an injectable local/test email-capture seam.
- Validate register -> verify -> login -> protected application before sign-off.

## Status
Architecture package / implementation blueprint. It is NOT a claim that the repository is already patched or tested.
